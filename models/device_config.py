#!/usr/bin/env python   
# -*- coding:utf-8 -*-

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TIMESTAMP, DECIMAL, ENUM, JSON
import sys
sys.path.append('../')
from models import Base

'''
device_config
id int 10 primary key
device_id int 10
data json
control json
updated_at timestamp
created_at timestamp
deleted_at timestamp nullable
null nullable
'''

class Device_config(Base):
	__tablename__ = 'device_config'

	id = Column(INTEGER(display_width = 10), primary_key = True)
	data = Column(JSON)
	control = Column(JSON)
	updated_at = Column(TIMESTAMP, nullable = False)
	created_at = Column(TIMESTAMP, nullable = False)
	deleted_at = Column(TIMESTAMP, nullable = True)

	device_id = Column(INTEGER(display_width = 10), ForeignKey('device.id'))
	device = relationship('Device', back_populates = 'device_configs')

	device_datas = relationship('Device_data', back_populates = 'device_config')