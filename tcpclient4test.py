#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
from tornado import ioloop, httpclient, gen
from tornado.gen import Task
from tornado.escape import native_str
import pdb, time, logging
import tornado.ioloop
import tornado.iostream
import logging
import socket
import json
import os

file_name = '/home/www/logo.png'
file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), file_name)
file_size = os.path.getsize(file_path)

class TCPClient(object):
	def __init__(self, host, port, io_loop=None):
		self.host = host
		self.port = port
		self.cache_size = 10 * 1024 # 10kb
		self.io_loop = io_loop
		self.shutdown = False
		self.stream = None
		self.sock_fd = None
	def get_stream(self):
		self.sock_fd = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
		self.stream = tornado.iostream.IOStream(self.sock_fd)
		self.stream.set_close_callback(self.on_close)
	def connect(self):
		self.get_stream()
		self.stream.connect((self.host, self.port), self.send_message)
	def on_receive(self, data):
		# message = json.loads(data)
		json_message = native_str(data.decode('UTF-8'))
		logging.info("Received: %s"%(json_message))
		print("Received: %s"%(json_message))
		dict_message = json.loads(json_message)
		if dict_message['method'] == 'push_param':
			logging.info('param_updated')
			# print('param_updated')
			message = {
				'device_id': 65,
				'method': 'param_updated'
			}
			data = json.dumps(message)
			self.stream.write(str.encode(data))
		if dict_message['method'] == 'push_image_ready':
			global file_path
			global file_size
			tmp_img_data = None
			with open(file_path, 'rb') as reader:
				tmp_img_data = reader.read(file_size)
			self.stream.write(tmp_img_data)
			self.stream.read_bytes(num_bytes = self.cache_size, callback = self.on_receive, partial=True)
		else:
			self.stream.close()
	def on_close(self):
		if self.shutdown:
			self.io_loop.stop()
	def send_message(self):
		logging.info("Send message....")
		global file_size
		'''
		message = {
			"device_id": 1234,
			"device_config_id": 100,
			"method": "push_image",
			"key": 'etateetawetwe',
			"size": file_size,
			'acquisition_time': 1479798817
		}

		message = {
			'device_id': 53,
			"method": 'pull_param'
		}

		'''
		message = {
			'device_id': 99,
			'device_config_id': 98,
			'method': 'push_data',
			'package': {
				1484447927: {
					'test1': {
						'value': 1
					},
					'test2': {
						'value': 2
					}
				},
				'1479798417': {
					'test3': {
						'value': 3
					},
					'test4': {
						'value': 4
					}
				}
			}
		}
                message={'device_id':1,'device_config_id':1,'method':'push_data','package':{'1606843867':{'FP_YX_TOTAL_SEND_NUM_1':{'value':0},'FP_YX_TOTAL_RECEIVE_NUM_1':{'value':0},'FP_YX__SEND_YES_NUM_1':{'value':0},'FP_YX_RECEIVE_YES_NUM_1':{'value':0},'FP_YX_MONEY_0':{'value':316.07},'FP_STATE_ENABLE_0':{'value':1},'FP_YX_SIGN_0':{'value':5},'FP_YX_NET_0':{'value':1},'FP_YX_DATA_NUM_0':{'value':0},'FP_SEND_STATE_0':{'value':0},'FP_REV_STATE_0':{'value':0},'FP_CHECK_NUM_0':{'value':0},'FP_DISTANCE':{'value':0}}}}
		data = json.dumps(message)
		self.stream.write(str.encode(data))
		self.stream.read_bytes(num_bytes = self.cache_size, callback = self.on_receive, partial=True)
		logging.info("After send....")
	def set_shutdown(self):
		self.shutdown = True
def main():
	io_loop = tornado.ioloop.IOLoop.instance()
	# client = TCPClient("123.57.60.239", 7800, io_loop)
	client = TCPClient("localhost", 9898, io_loop)
	client.connect()
	client.set_shutdown()
	io_loop.start()
if __name__ == "__main__":
	try:
		main()
	except Exception as e:
		logging.info("Ocurred Exception: %s" % str(e))
		# print("Ocurred Exception: %s" % str(e))
		quit()
