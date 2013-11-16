#!/usr/bin/env python
import MySQLdb

def connect(host, user, passwd, db):
        conn = MySQLdb.connect(host=host,user=user,passwd=passwd,db=db)

        return conn.cursor()
