#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import time
import datetime

def get_current_ts():
	return int(time.time())

def get_datetime_str_from_ts(ts):
	try:
		if isinstance(ts, float):
			ts = str(ts)
			ts = int(ts.split('.')[0])
		elif isinstance(ts, str):
			ts = int(ts.split('.')[0])
			# ts = int(ts)
		dt = datetime.datetime.fromtimestamp(ts)
		dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
		return dt_str
	except Exception as e:
		print(e)
		return ''

def string2json(string):
	pass

if __name__ == '__main__':
	ts = get_current_ts()
	print(ts)
	print(get_datetime_str_from_ts(ts))
	print(get_datetime_str_from_ts(str(ts)))
