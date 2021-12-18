#-*- coding:utf-8 -*-
# MariaDB Connection Option

import pymysql
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

class db_con:
  host = config['DBSET']['HOST']
  port = config['DBSET']['PORT']
  user = config['DBSET']['USER']
  passwd = config['DBSET']['PASSWD']
  db = config['DBSET']['DB']
  char = config['DBSET']['CHAR']
  
conn = pymysql.connect(host=db_con.host, port=db_con.port, user=db_con.user, password=db_con.passwd, db=db_con.db, charset=db_con.char, autocommit=True)
curs = conn.cursor(pymysql.cursors.DictCursor)