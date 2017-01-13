#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import redis
from commons.macro import *

def insert_into_redis(data, key):
	try:
		if data:
			redis_connection = redis.StrictRedis()
			redis_connection.lpush(key, json.dumps(data))
			return True
		else:
			return False
	except Exception as e:
		print e
		return False