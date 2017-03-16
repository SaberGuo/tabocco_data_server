#!/usr/bin/env python   
# -*- coding:utf-8 -*-

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, TIMESTAMP, DECIMAL, ENUM, JSON
import sys
sys.path.append('../')
from models import Base

'''
app table
id int 10 primary key
updated_at timestamp
created_at timestamp
deleted_at timestamp nullable
name varchar 50
null nullable
'''

class App(Base):
	__tablename__ = 'app'

	id = Column(INTEGER(display_width = 10), primary_key = True)
	updated_at = Column(TIMESTAMP, nullable = False)
	created_at = Column(TIMESTAMP, nullable = False)
	deleted_at = Column(TIMESTAMP, nullable = True)
	name = Column(VARCHAR(length = 50))

	stations = relationship('Station', back_populates = 'app')