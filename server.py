#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import logging
import argparse
import macro
import tornado
from tornado import ioloop
from tornado import stack_context
from tornado import gen
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tools import get_log_file_handler
import redis
from concurrent.futures import ThreadPoolExecutor
import json
import time


MAX_WORKERS = 2


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
		self.data_store = None
		self.encoder = json.JSONEncoder()
		self.DeviceID = ''
		self.image_size = 0
		self.image_time = 0
		self.stream = stream
		self.address = address
		self.io_loop = io_loop
		self.address_string = '{}:{}'.format(address[0], address[1])
		# self.address_family = stream.socket.family

		# 定义帧尾
		# self.EOF = b'test'

		self._clear_request_state()
		# self._message_callback = stack_context.wrap(self._on_message_receive_complete)
		self.stream.set_close_callback(stack_context.wrap(self._on_connection_close))
		# self._write_callback = self.close
		#从连接建立开始计时，如果连接超过macro中定义的TCP_CONNECTION_TIMEOUT，则服务端主动断开
		self.timeout_handle = self.io_loop.add_timeout(self.io_loop.time() + macro.TCP_CONNECTION_TIMEOUT, stack_context.wrap(self._on_timeout))
		# self.stream.read_until(self.EOF, stack_context.wrap(self._on_message_receive_complete))
		# self.stream.read_bytes(num_bytes = 10, callback=stack_context.wrap(self._on_message_receive_complete), partial=False)
		self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self._on_message_receive), partial=True)

	def _on_timeout(self):
		self.close()
		logging.info('{} connection timeout.'.format(self.address_string))
		# self.write(("Hello client!" + (self.EOF).decode()).encode())

	def _on_message_receive_complete(self, data):
		try:
			# timeout = 5
			# data = native_str(data.decode('latin1'))
			data = native_str(data.decode())
			logging.info("Received: %s", data)
			# self.write(data.encode(), stack_context.wrap(self.close))
			# self.io_loop.add_timeout(self.io_loop.time() + timeout, self._on_timeout)

		except Exception as ex:
			logging.error("Exception: %s", str(ex))

	def _on_message_receive(self, data):
		if self.data_store == None:
			self.data_store = data
		else:
			self.data_store += data
		try:
			data_str = self.data_store.decode()
			print(data_str)
			self.json_request = json.loads(data_str)
			if self.json_request.has_key('Method'):
				self.DeviceID = self.json_request['DeviceID']
				request = self.json_request['Method']
				if request == 'pullTime':
					self._on_pullTime_request()
				elif request == 'pushDatas':
					self._on_pushDatas_request(self.json_request)
				elif request == 'pullParams':
					self._on_pushParams_request()
				elif request == 'pushImage':
					self._on_pushImage_request(self.json_request)
				elif request == 'paramsUpdated':
					self.close()
			else:
				raise Exception('json request incomplete!')
		except Exception as e:
			print(e)
			self.json_request = {}
			self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self._on_message_receive), partial=True)

	def _on_pullTime_request(self):
		self.data_store = None
		self.write(int(time.time()), callback = stack_context.wrap(self.close))

	def _on_pushDatas_request(self, data):
		self.data_store = None
		redis_connection = redis.StrictRedis()
		redis_connection.lpush(macro.REDIS_LIST_KEY, self.encoder.encode(data))
		reply_data = {'DeviceID':self.DeviceID, 'Method':'dataUploaded'}
		self.write(self.encoder.encode(reply_data), callback = stack_context.wrap(self.close))

	def _on_pushParams_request(self):
		self.data_store = None
		control_data = {}
		self.write(self.encoder.encode(control_data), callback=stack_context.wrap(self._wait_pushParams_reply))

	def _wait_pushParams_reply(self):
		self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self._on_message_receive), partial=True)

	def _on_pushImage_request(self, data):
		self.data_store = None
		self.image_size = data['Package']['size']
		self.image_time = data['Package']['Millisecond']
		reply_data = {'DeviceID':self.DeviceID, 'Method':'pushImageReady'}
		self.write(self.encoder.encode(reply_data), callback = stack_context.wrap(self._start_receive_image_data))

	def _start_receive_image_data(self):
		self.stream.read_bytes(num_bytes = self.image_size, callback=stack_context.wrap(self._on_image_upload_complete), partial=False)

	def _on_image_upload_complete(self, data):
		image_package = {'deviceid':self.DeviceID, 'time':self.image_time, 'data':data}
		# image save operation
		reply_data = {'DeviceID':self.DeviceID, 'Method':'ImageUploaded'}
		self.write(self.encoder.encode(reply_data), callback = stack_context.wrap(self.close))

	def example(self):
		r = redis.StrictRedis()
		result = r.lpush('test')

	def _clear_request_state(self):
		"""Clears the per-request state.
		"""
		self._write_callback = None
		self._close_callback = None

	def set_close_callback(self, callback):
		"""Sets a callback that will be run when the connection is closed.
		"""
		self._close_callback = stack_context.wrap(callback)

	def _on_connection_close(self):
		if self.timeout_handle is not None:
			self.io_loop.remove_timeout(self.timeout_handle)
			self.timeout_handle = None
			print('here_on_connection_close')
		if self._close_callback is not None:
			callback = self._close_callback
			self._close_callback = None
			callback()
		self._clear_request_state()
		logging.info("{}:{} disconnect".format(self.address[0], self.address[1]))

	def close(self):
		self.stream.close()
		# Remove this reference to self, which would otherwise cause a 
		self._clear_request_state()

	def write(self, chunk, callback=None):
		"""Writes a chunk of output to the stream."""
		if not self.stream.closed():
			self._write_callback = stack_context.wrap(callback)
			self.stream.write(chunk, self._on_write_complete)

	def _on_write_complete(self):
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