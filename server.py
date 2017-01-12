#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import os
import time
import json
import redis
import tornado
import logging
import argparse
import commons.macro
from tornado import gen
from tornado import ioloop
from tornado import stack_context
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tools.db_tools import database_resource
from tools.log_tools import get_log_file_handler
from concurrent.futures import ThreadPoolExecutor

MAX_WORKERS = 6

class DataCollectionServer(TCPServer):
	def __init__(self, io_loop=None, **kwargs):
		TCPServer.__init__(self, io_loop=io_loop, **kwargs)

	def handle_stream(self, stream, address):
		TornadoTCPConnection(stream, address, io_loop=self.io_loop)


class TornadoTCPConnection(object):
	executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

	def __init__(self, stream, address, io_loop):
		print('Connected!!!!')
		self.json_request = {}
		# self.encoder = json.JSONEncoder()
		self.device_id = ''
		self.device_config_id = ''
		self.image_size = 0
		self.image_key = ''
		self.image_acquisition_time = 0
		self.stream = stream
		self.address = address
		self.io_loop = io_loop
		self.address_string = '{}:{}'.format(address[0], address[1])
		self.clear_request_state()
		self.stream.set_close_callback(stack_context.wrap(self.on_connection_close))
		#从连接建立开始计时，如果连接超过macro中定义的TCP_CONNECTION_TIMEOUT，则服务端主动断开
		self.timeout_handle = self.io_loop.add_timeout(self.io_loop.time() + macro.TCP_CONNECTION_TIMEOUT, stack_context.wrap(self.on_timeout))
		self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def on_timeout(self):
		self.close()
		logging.info('{} connection timeout.'.format(self.address_string))

	def on_message_receive(self, data):
		try:
			data_str = data.decode()
			print(data_str)
			self.json_request = json.loads(data_str)
			if self.json_request.has_key('method'):
				if self.device_id != '':
					self.device_id = self.json_request['device_id']
				request = self.json_request['method']
				elif request == 'push_data':
					self.on_push_data_request(self.json_request)
				elif request == 'pull_param':
					self.on_pull_param_request()
				elif request == 'push_image':
					self.on_push_image_request(self.json_request)
				elif request == 'param_updated':
					self.close()
			else:
				self.on_error_request()
		except Exception as e:
			print(e)
			self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def on_error_request(self):
		send_back = {'method':'failed','ts':int(time.time())}
		self.write(json.dumps(send_back), callback = stack_context.wrap(self.close))

	def on_push_data_request(self, request):
		redis_connection = redis.StrictRedis()
		device_config_id = request['device_config_id']
		for k, v in request['package'].iteritems():
			tmp_data = {}
			tmp_data['type'] = 'data'
			tmp_data['device_id'] = self.device_id
			tmp_data['device_config_id'] = device_config_id
			tmp_data['data'] = v
			tmp_data['ts'] = int(k)
			redis_connection.lpush(macro.REDIS_LIST_KEY, json.dumps(tmp_data))
		reply_data = {'device_id':self.device_id, 'method':'data_uploaded', 'ts':int(time.time())}
		# self.write(self.encoder.encode(reply_data), callback = stack_context.wrap(self.close))
		self.write(json.dumps(reply_data), callback = stack_context.wrap(self.close))

	def on_pull_param_request(self):
		param = {}
		with database_resource() as cursor:
			sql = 'select `%s`, `%s` from `%s` where `%s` = `%s`'%('id', 'data', 'device_config', 'device_id', self.device_id)
			cursor.execute(sql)
			value = cursor.fetchone()
			device_config_id = value[0]
			data = json.loads(value[1])
			param['device_id'] = self.device_id
			param['device_config_id'] = device_config_id
			param['method'] = 'push_param'
			param['config'] = data['config']
			param['control'] = data['control']
			param['ts'] = int(time.time())
		self.write(json.dumps(param), callback=stack_context.wrap(self.wait_push_param_reply))

	def wait_push_param_reply(self):
		self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def on_push_image_request(self, data):
		self.device_config_id = data['device_config_id']
		self.image_key = data['key']
		self.image_size = data['size']
		self.image_acquisition_time = data['acquisition_time']
		reply_data = {'device_id':self.device_id, 'method':'push_image_ready'}
		# self.write(self.encoder.encode(reply_data), callback = stack_context.wrap(self.start_receive_image_data))
		self.write(json.dumps(reply_data), callback = stack_context.wrap(self.start_receive_image_data))

	def start_receive_image_data(self):
		self.stream.read_bytes(num_bytes = self.image_size, callback=stack_context.wrap(self.on_image_upload_complete), partial=False)

	def on_image_upload_complete(self, data):
		redis_connection = redis.StrictRedis()
		file_path = os.path.abspath('./images/%s'%(self.device_id))
		if not os.path.exists(file_path):
			os.mkdir(file_path)
		url = os.path.join(file_path, '%s.jpg'%(str(self.image_acquisition_time)))
		image_value = {self.image_key:{'url':url}}
		tmp_data = {'type':'image', 'device_id':self.device_id, 'device_config_id':self.device_config_id, 'data':image_value, 'ts':self.image_acquisition_time}
		redis_connection.lpush(macro.REDIS_LIST_KEY, json.dumps(tmp_data))
		# image save operation
		with open(url, 'wb') as pen:
			pen.write(data)
		reply_data = {'device_id':self.device_id, 'method':'image_uploaded', 'ts':int(time.time())}
		self.write(json.dumps(reply_data), callback=stack_context.wrap(self.close))

	def clear_request_state(self):
		"""Clears the per-request state.
		"""
		self._write_callback = None
		self._close_callback = None

	def set_close_callback(self, callback):
		"""Sets a callback that will be run when the connection is closed.
		"""
		self._close_callback = stack_context.wrap(callback)

	def on_connection_close(self):
		if self.timeout_handle is not None:
			self.io_loop.remove_timeout(self.timeout_handle)
			self.timeout_handle = None
			print('here_on_connection_close')
		if self._close_callback is not None:
			callback = self._close_callback
			self._close_callback = None
			callback()
		self.clear_request_state()
		logging.info("{}:{} disconnect".format(self.address[0], self.address[1]))

	def close(self):
		self.stream.close()
		self.clear_request_state()

	def write(self, chunk, callback=None):
		"""Writes a chunk of output to the stream."""
		if not self.stream.closed():
			self._write_callback = stack_context.wrap(callback)
			self.stream.write(chunk, self.on_write_complete)

	def on_write_complete(self):
		if self._write_callback is not None:
			print('here_on_write_complete')
			callback = self._write_callback
			self._write_callback = None
			callback()


def main():
	parser = argparse.ArgumentParser(description='custom_tcp_server')
	parser.add_argument('-p', '--port', type=int, 
		help='port to listen')
	args = parser.parse_args()
	logging.basicConfig(level=logging.INFO)
	log = logging.getLogger()
	log.addHandler(get_log_file_handler("port:" + str(args.port)))
	server = DataCollectionServer()
	server.listen(args.port)
	ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	try:
		main()
	except Exception as ex:
		print ("Ocurred Exception: %s" % str(ex))
		quit()