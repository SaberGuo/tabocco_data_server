#!/usr/bin/env python
# coding=utf-8

import sys
import json
import random
import logging
import mysql.connector
sys.path.append('../')
from commons.macro import *
from tools.common_tools import get_current_ts
from tools.upyun_tools import save_to_upyun

def create_engine(user, password, database, host = '127.0.0.1', port = 3306, **kw):
    params = dict(user = user, password = password, database = database, host = host, port = port)
    defaults = dict(use_unicode = True, charset = 'utf8', collation = 'utf8_general_ci', autocommit = False)
    for k, v in defaults.items():
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

def get_latest_device_config_json(device_id):
    try:
        if not isinstance(device_id, int):
            device_id = int(device_id)
        param = {}
        with database_resource() as cursor:
            sql = 'select `%s`, `%s`, `%s` from `%s` where `%s` = %d order by id desc'%('id', 'data', 'control', 'device_config', 'device_id', device_id)
            cursor.execute(sql)
            value = cursor.fetchone()
            device_config_id = value[0]
            data = json.loads(value[1])
            control = json.loads(value[2])
            param['device_id'] = device_id
            param['device_config_id'] = device_config_id
            param['method'] = 'push_param'
            param['config'] = data
            param['control'] = control
            param['ts'] = get_current_ts()
        return json.dumps(param)
    except Exception as e:
        logging.info(e)
        # print(e)
        return None

def save_json_data(json_data):
    try:
        dict_data = json.loads(json_data)
        if not isinstance(dict_data['device_id'], int):
            dict_data['device_id'] = int(dict_data['device_id'])
        if not isinstance(dict_data['device_config_id'], int):
            dict_data['device_config_id'] = int(dict_data['device_config_id'])
        db_name = ''
        with database_resource() as cursor:
            if dict_data['type'] == 'image':
                db_name = 'device_data'
                # db_name = 'device_image'
                if save_to_upyun(dict_data):
                    sql = "insert into `%s` (`device_id`, `device_config_id`, `ts`, `data`) values \
                                (%d, %d, '%s', '%s')"%(db_name, dict_data['device_id'], dict_data['device_config_id'], dict_data['ts'], json.dumps(dict_data['data']))
                    cursor.execute(sql)
            else:
                db_name = 'device_data'
                sql = "insert into `%s` (`device_id`, `device_config_id`, `ts`, `data`) values \
                            (%d, %d, '%s', '%s')"%(db_name, dict_data['device_id'], dict_data['device_config_id'], dict_data['ts'], json.dumps(dict_data['data']))
                cursor.execute(sql)
            print('after execution')
            logging.info('after execution')
    except Exception as e:
        logging.info(e)
        print(e)
        pass


def _save_device_config(data):
    device_id = data['device_id']
    config = json.dumps(data['config'])
    control = json.dumps(data['control'])
    with database_resource() as cursor:
        sql = "insert into `%s` (`device_id`, `data`, `control`) \
        values (%d, '%s', '%s')"%('device_config' ,device_id, config, control)
        cursor.execute(sql)

if __name__ == '__main__':
    # control = {
    #     "img_capture_invl": "*/30 * * * *",
    #     "img_upload_invl": "*/30 * * * *",
    #     "data_capture_invl": "*/30 * * * *",
    #     "data_upload_invl": "*/30 * * * *"
    # }
    # config = {
    #     "t_30": {
    #         "port": "AD1",
    #         "unit": "x",
    #         "type": "temperature",
    #         "desc": "30depth temperature"
    #     },
    #     "t_10": {
    #         "port": "AD2",
    #         "unit": "x",
    #         "type": "temperature",
    #         "desc": "10depth temperature"
    #     }
    # }
    config = {
        't_30': {
            'port': 'AD1',
            'unit': 'x',
            'type': 'temperature',
            'desc': '30depth temperature',
            'max_v': 100,
            'min_v': 0
        },
        't_10': {
            'port': 'AD2',
            'unit': 'x',
            'type': 'temperature',
            'desc': '10depth temperature',
            'max_v': 100,
            'min_v': 0
        }
    }
    control = {
        'img_capture_invl': '*/30 * * * *',
        'img_upload_invl': '*/30 * * * *',
        'data_capture_invl': '*/30 * * * *',
        'data_upload_invl': '*/30 * * * *'
    }
    device_config_data_to_save = {
        'device_id': random.randint(0,100),
        'config': config,
        'control': control
    }
    _save_device_config(device_config_data_to_save)
    device_config_data_query = get_latest_device_config_json(65)
    print(device_config_data_query)
    # json_data_to_save = json.dumps({
    #     "type": "data",
    #     "device_config_id": 1,
    #     "device_id": 1,
    #     "data": {
    #         "t_30": {
    #             "value": 5
    #         }
    #     },
    #     "ts": "2017-01-07 16:33:54"
    # })
    json_data_to_save = json.dumps({
        'type': 'data',
        'device_config_id': 1,
        'device_id': 1,
        'data': {
            't_30': {
                'value': 5
            }
        },
        'ts': '2017-01-07 16:33:54'
    })

    save_json_data(json_data_to_save)
