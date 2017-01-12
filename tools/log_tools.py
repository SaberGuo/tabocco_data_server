#!/usr/bin/env python   
# -*- coding:utf-8 -*-

import logging
import time
from logging.handlers import TimedRotatingFileHandler


def get_log_file_handler(filename_prefix):
    #日志打印格式
    log_fmt = '%(asctime)s\tFile \"%(filename)s\",line %(lineno)s\t%(levelname)s: %(message)s'
    formatter = logging.Formatter(log_fmt)
    #创建TimedRotatingFileHandler对象
    log_file_handler = TimedRotatingFileHandler(filename=filename_prefix, when="D", interval=1, backupCount=5)
    #log_file_handler.suffix = "%Y-%m-%d_%H-%M.log"
    #log_file_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}.log$")
    log_file_handler.setFormatter(formatter)    
    # logging.basicConfig(level=logging.INFO)
    # log = logging.getLogger()
    # log.addHandler(log_file_handler)

    return log_file_handler