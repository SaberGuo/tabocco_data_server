#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import os

def check_device_img_file(device_id, create_if_noexists = True):
	filepath = os.path.abspath('./images/%s'%(device_id))
	if not os.path.exists(filepath):
		if create_if_noexists:
			os.mkdir(file_path)
	return filepath

def get_image_url_local(filepath, image_acquisition_time):
	url = os.path.join(filepath, '%s.jpg'%(str(image_acquisition_time)))
	return url

def get_image_url_server():
	pass