#!/usr/bin/env python
# coding=utf-8

import json
import mysql.connector
from commons.macro import *
from tools.common_tools import get_current_ts

def create_engine(user, password, database, host = '127.0.0.1', port = 3306, **kw):
    params = dict(user = user, password = password, database = database, host = host, port = port)
    defaults = dict(use_unicode = True, charset = 'utf8', collation = 'utf8_general_ci', autocommit = False)
    for k, v in defaults.iteritems():
        params[k] = kw.pop(k, v)
    params.update(kw)
    params['buffered'] = True
    engine = mysql.connector.connect(**params)
    return engine

class database_resource:
    def __init__(self, user=DATA_DB_USER, password=DATA_DB_PASSWORD, database=DATA_DB_NAME, host=DB_HOST, port=DB_HOST_PORT):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
    def __enter__(self):
        self.conn = create_engine(self.user, self.password, self.database, self.host, self.port)
        self.cursor = self.conn.cursor()
        return self.cursor
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.cursor.close()
        self.conn.close()

def get_latest_device_config(device_id):
    try:
        param = {}
        with database_resource() as cursor:
            sql = 'select `%s`, `%s` from `%s` where `%s` = `%s` order by id desc'%('id', 'data', 'device_config', 'device_id', device_id)
            cursor.execute(sql)
            value = cursor.fetchone()
            device_config_id = value[0]
            data = json.loads(value[1])
            param['device_id'] = device_id
            param['device_config_id'] = device_config_id
            param['method'] = 'push_param'
            param['config'] = data['config']
            param['control'] = data['control']
            param['ts'] = get_current_ts()
        return json.dumps(param)
    except Exception as e:
        print e
        return None