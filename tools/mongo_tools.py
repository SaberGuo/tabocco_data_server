#!/usr/bin/env python
# coding=utf-8
import sys
sys.path.append('../')
import logging
from commons.macro import *
from pymongo import MongoClient

def create_mongo_engine(dbname, host="localhost", port=27017, user="", password=""):
    client = MongoClient(host, port)
    if user!= "":
        db = client.admin
        db.authenticate(user, password)
        return client, db[dbname]
    else:
        return client, client[dbname]

class mongodb_resource:
    def __init__(self, user=MONGO_DB_USER, password=MONGO_DB_PASSWORD, database=MONGO_DB_NAME, host=MONGO_DB_HOST, port=MONGO_DB_HOST_PORT):
        self.user = user
        self.password = password
        self.database = database
        self.host = host
        self.port = port
    def __enter__(self):
        self.client, self.db = create_mongo_engine(self.database, self.host, self.port, self.user, self.password)
        return self.db
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

def insert_mongo_data(json_data):
    logging.info("insert mongo data")
    with mongodb_resource() as db:
        db.datas.insert(json_data)

def insert_mongo_image(json_image):
    logging.info("insert mongo image")
    with mongodb_resource() as db:
        db.images.insert(json_image)

if __name__ == "__main__":
   json_data = {"test":"ttt"}
   with mongodb_resource() as db:
       db.data.insert(json_data) 
