#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import sys
import redis
sys.path.append('../')
from commons.macro import *
from tools.server_tools import *

def insert_into_redis(data, key):
	print(key)
	try:
		if data:
			redis_connection = redis.StrictRedis()
			redis_connection.lpush(key, json.dumps(data))
			print('insert_into_redis')
			print(json.dumps(data))
			return True
		else:
			return False
	except Exception as e:
		print(e)
		return False

if __name__ == '__main__':
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
	print(data_to_save)
	insert_into_redis(data_to_save, 'redis_list_key_1')