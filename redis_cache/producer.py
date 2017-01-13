#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import redis
from commons.macro import *

def insert_into_redis(data):
	redis_connection = redis.StrictRedis()
	redis_connection.lpush(REDIS_LIST_KEY, json.dumps(data))