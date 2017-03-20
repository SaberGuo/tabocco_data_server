#!/usr/bin/env python
# -*- coding:utf-8 -*-


import sys
from datetime import *
sys.path.append('../')
from models import Database_session, Station, Device, Device_data


def status_check(threshold):
    with Database_session() as session:
        stations = session.query(Station).all()
        # print(len(stations))
        for station in stations:
            station.status = 'normal'
            devices = station.devices
            for device in devices:
                device.status = 'normal'
                device_lastest_data = session.query(Device_data).filter_by(device_id = device.id).order_by(Device_data.created_at.desc()).first()
                if device_lastest_data is None:
                    device.status = 'abnormal'
                    station.status = 'abnormal'
                    continue
                tmp = datetime.utcnow() + timedelta(hours=8) - device_lastest_data.created_at # Beijing timezone 8 hours later than utc zone !
                if tmp > timedelta(threshold):
                    device.status = 'abnormal'
                    station.status = 'abnormal'


if __name__ == '__main__':
       status_check(1)
       print('check finish !')
