#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import logging
import argparse
import macro
import asyncio
import asyncio_redis
import tornado
from tornado import ioloop
from tornado import stack_context
from tornado import gen
from tornado.escape import native_str
from tornado.tcpserver import TCPServer
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.platform.asyncio import to_tornado_future
from tools import get_log_file_handler
import redis
from concurrent.futures import ThreadPoolExecutor


MAX_WORKERS = 2


class TornadoTCPServer(TCPServer):
	def __init__(self, io_loop=None, **kwargs):
		TCPServer.__init__(self, io_loop=io_loop, **kwargs)

	def handle_stream(self, stream, address):
		TornadoTCPConnection(stream, address, io_loop=self.io_loop)


class TornadoTCPConnection(object):
	executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

	def __init__(self, stream, address, io_loop):

		print('Connected!!!!')

		self.stream = stream
		self.address = address
		self.io_loop = io_loop
		self.address_string = '{}:{}'.format(address[0], address[1])
		# self.address_family = stream.socket.family
		# 定义帧尾
		self.EOF = b'test'
		self._clear_request_state()
		# self._message_callback = stack_context.wrap(self._on_message_receive_complete)
		self.stream.set_close_callback(stack_context.wrap(self._on_connection_close))
		# self._write_callback = self.close
		#从连接建立开始计时，如果连接超过macro中定义的TCP_CONNECTION_TIMEOUT，则服务端主动断开
		self.timeout_handle = self.io_loop.add_timeout(self.io_loop.time() + macro.TCP_CONNECTION_TIMEOUT, stack_context.wrap(self._on_timeout))
		# self.stream.read_until(self.EOF, self._message_callback)
		self.stream.read_until(self.EOF, stack_context.wrap(self._on_message_receive_complete))

	def _on_timeout(self):
		self.close()
		logging.info('{} connection timeout.'.format(self.address_string))
		# self.write(("Hello client!" + (self.EOF).decode()).encode())

	@gen.coroutine
	def _on_message_receive_complete(self, data):
		try:
			# timeout = 5
			# data = native_str(data.decode('latin1'))
			data = native_str(data.decode())
			logging.info("Received: %s", data)
			result = yield self.background_wait_task()
			print(result)
			# self.example()
			self.write(data.encode(), stack_context.wrap(self.close))
			# self.io_loop.add_timeout(self.io_loop.time() + timeout, self._on_timeout)
			# redis write operation
			# redis read operation'

		except Exception as ex:
			logging.error("Exception: %s", str(ex))

	def example(self):
		r = redis.StrictRedis()
		result = r.blpop('test')

	def background_wait_task(self):
		future = TornadoTCPConnection.executor.submit(self.example)
		future = to_tornado_future(future)
		return future

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
	server = TornadoTCPServer()
	server.listen(args.port)
	ioloop.IOLoop.instance().start()
	# AsyncIOMainLoop().install()
	# asyncio.get_event_loop().run_forever().start()

if __name__ == "__main__":
	try:
		main()
	except Exception as ex:
		print ("Ocurred Exception: %s" % str(ex))
		quit()