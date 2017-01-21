#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import json
import tornado
import logging
import argparse
from tools import *
from commons.macro import *
from redis_cache import producer
from tornado import gen, ioloop, stack_context
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor


# def handler_exception(handle_func):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kw):
#         	try:
#         		func(*args, **kw)
#         	except Exception as e:
#         		print(e)
#         		print('wrappers')
#         		handle_func()
#         return wrapper
#     return decorator

class DataCollectionServer(TCPServer):
	def __init__(self, io_loop=None, **kwargs):
		TCPServer.__init__(self, io_loop=io_loop, **kwargs)

	def handle_stream(self, stream, address):
		TornadoTCPConnection(stream, address, io_loop=self.io_loop)


class TornadoTCPConnection(object):
	MAX_SIZE = 10 * 1024 #10KB
	MAX_WORKERS = 10
	executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

	def __init__(self, stream, address, io_loop):
		self.json_request = {}
		self.stream = stream
		self.address = address
		self.io_loop = io_loop
		self.address_string = '{}:{}'.format(address[0], address[1])
		logging.info('connected from %s'%(self.address_string))
		self.clear_request_state()
		self.stream.set_close_callback(stack_context.wrap(self.on_connection_close))
		self.timeout_handle = self.io_loop.add_timeout(self.io_loop.time() + TCP_CONNECTION_TIMEOUT, stack_context.wrap(self.on_timeout))
		self.stream.read_bytes(num_bytes = TornadoTCPConnection.MAX_SIZE, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def wait_new_reqeust(self):
		self.stream.read_bytes(num_bytes = TornadoTCPConnection.MAX_SIZE, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def on_timeout(self):
		self.close()
		logging.info('{} connection timeout.'.format(self.address_string))

	def on_message_receive(self, data):
		try:
			data_str = native_str(data.decode('UTF-8'))
			logging.info(data_str)
			# print(data_str)
			tmp = json.loads(data_str)
			for k, v in tmp.items():
				# if not self.json_request.__contains__(k):
				self.json_request[k] = v
			if self.json_request.__contains__('method'):
				request = self.json_request['method']
				if request == 'push_data':
					self.on_push_data_request(self.json_request)
				elif request == 'pull_param':
					self.on_pull_param_request(self.json_request)
				elif request == 'push_image':
					# print('push_image')
					logging.info('push_image')
					self.on_push_image_request(self.json_request)
				elif request == 'param_updated':
					logging.info('param_updated')
					# print('param_updated')
					self.close()
				elif request == 'close_connection':
					logging.info('close_connection')
					# print('close_connection')
					self.close()
			else:
				self.on_error_request()
		except Exception as e:
			logging.info(e)
			# print(e)
			self.on_error_request()

	def on_push_data_request(self, request):
		for ts, data in request['package'].items():
			producer.insert_into_redis(get_data_to_save(request, ts, data), REDIS_LIST_KEY)
		# self.stream.write(str.encode(get_reply_json(self.json_request)), callback = stack_context.wrap(self.wait_new_reqeust))
		self.stream.write(str.encode(get_reply_json(self.json_request)), callback = stack_context.wrap(self.close))
			
	@run_on_executor
	def on_pull_param_request(self, request):
		param = get_latest_device_config_json(request['device_id'])
		if param:
			self.stream.write(str.encode(param), callback=stack_context.wrap(self.wait_push_param_reply))
		else:
			self.on_error_request()

	def wait_push_param_reply(self):
		self.stream.read_bytes(num_bytes = TornadoTCPConnection.MAX_SIZE, callback=stack_context.wrap(self.on_message_receive), partial=True)

	def on_push_image_request(self, request):
		num_bytes = self.json_request['size']
		if isinstance(num_bytes, int) and num_bytes > 0: 
			self.stream.write(str.encode(get_reply_json(self.json_request)), callback = stack_context.wrap(self.start_receive_image_data))
		else:
			self.on_error_request()

	def start_receive_image_data(self):
		self.json_request['method'] = 'pushing_image'
		# print('start_receive_image_data')
		logging.info('start_receive_image_data')
		self.stream.read_bytes(num_bytes = self.json_request['size'], callback=stack_context.wrap(self.on_image_upload_complete), partial=False)

	@run_on_executor
	def on_image_upload_complete(self, data):
		try:
			filepath = check_device_img_file(self.json_request['device_id'])
			url = get_image_url_local(filepath, self.json_request['acquisition_time'])
			save_image_local(data, url)
			self.json_request['image_info'] = {self.json_request['key']:{'url':url}}
			tmp_data = get_image_info_to_save(self.json_request)
			if producer.insert_into_redis(tmp_data, REDIS_LIST_KEY):
				# self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.close))
				self.stream.write(str.encode(get_reply_json(self.json_request)), callback=stack_context.wrap(self.wait_new_reqeust))
			else:
				self.on_error_request()
		except Exception as e:
			logging.info(e)
			# print(e)
			self.on_error_request()

	def on_error_request(self):
		# self.stream.write(str.encode(get_reply_json(is_failed = True)), callback = stack_context.wrap(self.wait_new_reqeust))
		self.stream.write(str.encode(get_reply_json(is_failed = True)), callback = stack_context.wrap(self.close))

	def clear_request_state(self):
		self._close_callback = None

	def set_close_callback(self, callback):
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
	log.addHandler(get_log_file_handler("port:" + str(args.port) + ".log"))
	server = DataCollectionServer()
	server.listen(args.port)
	ioloop.IOLoop.instance().start()

if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		logging.info("ocurred Exception: %s" % str(e))
		# print ("ocurred Exception: %s" % str(e))
		quit()