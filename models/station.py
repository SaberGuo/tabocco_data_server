#!/usr/bin/env python   
# -*- coding:utf-8 -*-

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TIMESTAMP, DECIMAL, ENUM, JSON
import sys
sys.path.append('../')
from models import Base

'''
station
id int 10 primary key
app_id int 10
name varchar 50
type varchar 50
location varchar 100
lat decimal 10
lon decimal 11
alt decimal 8
status enum
updated_at timestamp
created_at timestamp
deleted_at timestamp nullable
null nullable
'''

class Station(Base):
	__tablename__ = 'station'
	id = Column(INTEGER(display_width = 10), primary_key = True)
	name = Column(VARCHAR(length = 50))
	type = Column(VARCHAR(length = 50))
	location = Column(VARCHAR(length = 100))
	lat = Column(DECIMAL)
	lon = Column(DECIMAL)
	alt = Column(DECIMAL)
	status = Column(ENUM('normal', 'abnormal'))
	updated_at = Column(TIMESTAMP, nullable = False)
	created_at = Column(TIMESTAMP, nullable = False)
	deleted_at = Column(TIMESTAMP, nullable = True)

	app_id = Column(INTEGER(display_width = 10), ForeignKey('app.id'))
	app = relationship('App', back_populates="stations")

	devices = relationship('Device', back_populates = 'station')