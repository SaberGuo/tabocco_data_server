#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import json
from tools.common_tools import *

def get_reply(request, is_failed = False):
	try:
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
		return json.dumps(reply)
	finally:
		return json.dumps({'method':'failed','ts':get_current_ts()})

def get_data_to_save(request, ts, data):
	try:
		tmp_data = {}
		tmp_data['type'] = 'data'
		tmp_data['device_id'] = request['device_id']
		tmp_data['device_config_id'] = request['device_config_id']
		tmp_data['data'] = data
		tmp_data['ts'] = get_datetime_str_from_ts(ts)
		return tmp_data
	except Exception as e:
		print e
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
		print e
		return None