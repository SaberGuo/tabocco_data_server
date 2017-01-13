#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import json
import redis
import commons.macro
import argparse
from tools.db_tools import database_resource

class RedisConsumer(object):
	"""docstring for RedisConsumer"""
	def __init__(self, db=None, key=None, host='localhost', port=6379):
		super(RedisConsumer, self).__init__()
		self.redis_connection = redis.StrictRedis(host=host, port=port, db=db if db else macro.REDIS_DB_NUM)
		self.key = key if key else macro.REDIS_LIST_KEY

	def start(self):
		while True:
			item=self.redis_connection.blpop(self.key)
			data = json.loads(item[1])
			sql = ''
			db_name = ''
			with database_resource() as cursor:
				if data['type'] = 'image':
					db_name = 'device_image'
					
				else:
					db_name = 'device_data'
				sql = 'insert into `%s` (`device_id`, `device_config_id`, `ts`, `data`) values \
					(`%s`, `%s`, `%s`, `%s`)'%(db_name, data['device_id'], data['device_config_id'], data['ts'], json.dumps(data['data']))
				cursor.execute(sql)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='redis_consumer')
	parser.add_argument('--db', type=int, 
		help='redis db num', default=None)
	parser.add_argument('--key', type=str, 
		help='read list key', default=None)
	parser.add_argument('--host', type=str, 
		help='address list key', default='localhost')
	parser.add_argument('--port', type=int, 
		help='port to connect', default=6379)
	args = parser.parse_args()
	redis_consumer = RedisConsumer(args.db, args.key, args.host, args.port)
	try:
		redis_consumer.start()
	except KeyboardInterrupt:
		pass