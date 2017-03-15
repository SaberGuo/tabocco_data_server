#!/usr/bin/env python
# -*- coding:utf-8 -*-

import os
# from PIL import Image

def save_image_local(data, url):
	if not os.path.exists(url):
		with open(url, 'wb') as pen:
			pen.write(data)

def save_image_server(data, url):
	pass
