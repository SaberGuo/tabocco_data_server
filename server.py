#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import json
import tornado
import logging
import argparse
from commons.macro import *
from tornado import gen, ioloop, stack_context
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tools import *
from concurrent.futures import ThreadPoolExecutor
from redis_cache import producer
# import sys
# from imp import reload
# reload(sys)
# sys.setdefaultencoding('utf-8')


class DataCollectionServer(TCPServer):
	def __init__(self, io_loop=None, **kwargs):
		TCPServer.__init__(self, io_loop=io_loop, **kwargs)

	def handle_stream(self, stream, address):
		TornadoTCPConnection(stream, address, io_loop=self.io_loop)


class TornadoTCPConnection(object):
	MAX_WORKERS = 10
	executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

	def __init__(self, stream, address, io_loop):
		print('connected!')
		self.json_request = {}
		self.stream = stream
		self.address = address
		self.io_loop = io_loop
		self.address_string = '{}:{}'.format(address[0], address[1])
		self.clear_request_state()
		self.stream.set_close_callback(stack_context.wrap(self.on_connection_close))
		self.timeout_handle = self.io_loop.add_timeout(self.io_loop.time() + TCP_CONNECTION_TIMEOUT, stack_context.wrap(self.on_timeout))
		self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def on_timeout(self):
		self.close()
		logging.info('{} connection timeout.'.format(self.address_string))

	def on_message_receive(self, data):
		try:
			data_str = native_str(data.decode('UTF-8'))
			print(data_str)
			tmp = json.loads(data_str)
			for k, v in tmp.items():
				if not self.json_request.__contains__(k):
					self.json_request[k] = v
			if self.json_request.__contains__('method'):
				request = self.json_request['method']
				if request == 'push_data':
					self.on_push_data_request(self.json_request)
				elif request == 'pull_param':
					self.on_pull_param_request(self.json_request)
				elif request == 'push_image':
					self.on_push_image_request(self.json_request)
				elif request == 'param_updated':
					self.close()
			else:
				self.on_error_request()
		except Exception as e:
			print(e)
			self.on_error_request()

	def on_push_data_request(self, request):
		flag = True
		for ts, data in request['package'].items():
			print(ts)
			print(data)
			# flag = flag or (producer.insert_into_redis(get_data_to_save(request, ts, data), REDIS_LIST_KEY))
			producer.insert_into_redis(get_data_to_save(request, ts, data), REDIS_LIST_KEY)
		if flag:
			self.stream.write(str.encode(get_reply_json(self.json_request)), callback = stack_context.wrap(self.close))
		else:
			self.on_error_request()

	def on_pull_param_request(self, request):
		param = get_latest_device_config_json(request['device_id'])
		if param:
			self.stream.write(str.encode(param), callback=stack_context.wrap(self.wait_push_param_reply))
		else:
			self.on_error_request()

	def wait_push_param_reply(self):
		self.stream.read_bytes(num_bytes = 512, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def on_push_image_request(self, request):
		self.stream.write(str.encode(get_reply_json(self.json_request)), callback = stack_context.wrap(self.start_receive_image_data))

	def start_receive_image_data(self):
		self.json_request['method'] = 'pushing_image'
		self.stream.read_bytes(num_bytes = self.json_request['size'] * 1024, callback=stack_context.wrap(self.on_image_upload_complete), partial=False)

	def on_image_upload_complete(self, data):
		filepath = check_device_img_file(self.json_request['device_id'])
		url = get_image_url_local(filepath, self.json_request['acquisition_time'])
		save_image_local(data, url)
		self.json_request['image_info'] = {self.json_request['key']:{'url':url}}
		tmp_data = get_image_info_to_save(self.json_request)
		if producer.insert_into_redis(tmp_data, REDIS_LIST_KEY):
			self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.close))
		else:
			self.on_error_request()

	def on_error_request(self):
		self.stream.write(str.encode(get_reply_json(is_failed = True)), callback = stack_context.wrap(self.close))

	def clear_request_state(self):
		"""Clears the per-request state.
		"""
		self._close_callback = None

	def set_close_callback(self, callback):
		"""Sets a callback that will be run when the connection is closed.
		"""
		self._close_callback = stack_context.wrap(callback)

	def on_connection_close(self):
		if self.timeout_handle is not None:
			self.io_loop.remove_timeout(self.timeout_handle)
			self.timeout_handle = None
		if self._close_callback is not None:
			callback = self._close_callback
			self._close_callback = None
			callback()
		self.clear_request_state()
		logging.info("{}: disconnect".format(self.address_string))

	def close(self):
		self.stream.close()


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
		print ("ocurred Exception: %s" % str(ex))
		quit()