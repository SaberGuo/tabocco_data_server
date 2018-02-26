#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import redis
import json
import logging
sys.path.append('../')
from commons import macro
from tools.common_tools import *
from tools.db_tools import *
from redis_cache import email_producer

def get_reply_json(request = None, is_failed = False):
	try:
		print('line 1')
		reply = {}
		if is_failed:
			reply = {'method':'failed','ts':get_current_ts()}
		else:
			method = request['method']
			reply = {'device_id':request['device_id'], 'method':'', 'ts':get_current_ts()}
			if method == 'push_data':
				reply['method'] = 'data_uploaded'
			if method == 'push_image':
				reply['method'] = 'push_image_ready'
			if method == 'pushing_image':
				reply['method'] = 'image_uploaded'
                        if method == 'push_data_size':
				print('here in get_reply_json')
				reply['method'] = 'push_data_ready'
			if method == 'update_device_info':
				reply['method'] = 'update_device_info'
			if method == 'update_time':
				reply = {'ts':get_current_ts()}
		reply_str = json.dumps(reply)
		email_producer.insert_into_redis(reply_str, macro.EMAIL_REDIS_LIST_KEY)
		return reply_str
	except Exception as e:
		logging.info(e)
		print(e)
		return json.dumps({'method':'failed','ts':get_current_ts()})

def get_data_to_save(request, ts, data):
	try:
		tmp_data = {}
		tmp_data['type'] = 'data'
		tmp_data['device_id'] = request['device_id']
		tmp_data['device_config_id'] = request['device_config_id']
		tmp_data['data'] = data
		tmp_data['ts'] = get_datetime_str_from_ts(ts)
		# print(tmp_data)
		return tmp_data
	except Exception as e:
		logging.info(e)
		email_producer.insert_into_redis(e, macro.EMAIL_REDIS_LIST_KEY)
		# print(e)
		return None

def get_image_info_to_save(request):
	try:
		if request:
			tmp_data = {}
			tmp_data['type'] = 'image'
			tmp_data['device_id'] = request['device_id']
			tmp_data['device_config_id'] = request['device_config_id']
			tmp_data['data'] = request['image_info']
			tmp_data['ts'] = get_datetime_str_from_ts(request['acquisition_time'])
			return tmp_data
		else:
			return None
	except Exception as e:
		logging.info(e)
		email_producer.insert_into_redis(e, macro.EMAIL_REDIS_LIST_KEY)
		# print(e)
		return None

if __name__ == '__main__':
	# get_reply_json
	print(get_reply_json(is_failed = True))
	print(get_reply_json({"method": "push_data", "device_id": 1}))
	print(get_reply_json({"method": "push_image", "device_id": 1}))
	print(get_reply_json({"method": "pushing_image", "device_id": 1}))
	# get_data_to_save
	request = {
		'device_id': 1,
		'device_config_id': 1,
	}
	ts = '1484391385'
	data = {
		't_30': {
			'value': 5
		}
	}
	data_to_save = get_data_to_save(request, ts, data)
	redis_connection = redis.StrictRedis()
	redis_connection.lpush('redis_list_key_1', json.dumps(data_to_save))
	item=redis_connection.blpop('redis_list_key_1')
	json_data = item[1]
	save_json_data(json_data)
	# get_image_info_to_save
	request = {
		'device_id': 1,
		'device_config_id': 1,
		'image_info': {
			'user_defined_key': {
				'url':'/root/home/project/images/1/1.jpg'
			}
		},
		'acquisition_time': 1484391381
	}
	image_info_to_save = get_image_info_to_save(request)
	redis_connection = redis.StrictRedis()
	redis_connection.lpush('redis_list_key_1', json.dumps(image_info_to_save))
	item=redis_connection.blpop('redis_list_key_1')
	json_data = item[1]
	save_json_data(json_data)
