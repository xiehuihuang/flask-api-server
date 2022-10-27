#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: config.py
# @time: 2020/9/15 16:16
# @author: jack
# @Email: 793936517@qq.com
# @desc:
import os
import configparser

from main.constant import *

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SERVER_ENV = os.getenv('SERVER_ENV')
_CONFIG = configparser.ConfigParser()
_CONFIG.read(os.path.join(BASE_DIR, "conf/config.ini"), encoding='utf-8')


DEBUG = _CONFIG.getboolean("default", "debug")
SECRET_KEY = r"9TIgUjXMddft2lzDzN7seo3j8QCAGBa3"


class MySQLConf:
    host = _CONFIG.get("mysql", "host")
    port = _CONFIG.getint("mysql", "port")
    user = _CONFIG.get("mysql", "user")
    password = _CONFIG.get("mysql", "password")
    db = _CONFIG.get("mysql", "db")
    charset = _CONFIG.get("mysql", "charset")
    maxconnections = _CONFIG.getint("mysql", "maxconnections")
    pool_recycle = _CONFIG.getint("mysql", "pool_recycle")
    pool_size = _CONFIG.getint("mysql", "pool_size")


class PgSQLConf:
    host = _CONFIG.get("pgsql", "host")
    port = _CONFIG.getint("pgsql", "port")
    user = _CONFIG.get("pgsql", "user")
    password = _CONFIG.get("pgsql", "password")
    db = _CONFIG.get("pgsql", "db")
    charset = _CONFIG.get("pgsql", "charset")
    maxconnections = _CONFIG.getint("pgsql", "maxconnections")
    pool_recycle = _CONFIG.getint("pgsql", "pool_recycle")
    pool_size = _CONFIG.getint("pgsql", "pool_size")


class RedisConf:
    host = _CONFIG.get("redis", "host")
    port = _CONFIG.getint("redis", "port")
    db1 = _CONFIG.getint("redis", "db1")
    db2 = _CONFIG.getint("redis", "db2")
    password = _CONFIG.get("redis", "password")
    expires = _CONFIG.getint("redis", "expires")


SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MySQLConf.user}:{MySQLConf.password}@{MySQLConf.host}:{MySQLConf.port}/{MySQLConf.db}"

# SQLALCHEMY_BINDS 可配置多数据库连接
# SQLALCHEMY_BINDS = {
#     "data_warehouse": f"postgresql+psycopg2://{PgSQLConf.user}:{PgSQLConf.password}@{PgSQLConf.host}:{PgSQLConf.port}/{PgSQLConf.db}",
# }
SQLALCHEMY_TRACK_MODIFICATIONS = _CONFIG.getboolean("sqlalchemy", "track_modifications")
# SQLALCHEMY_COMMIT_ON_TEARDOWN = _CONFIG.getboolean("sqlalchemy", "commit_on_teardown")  # This session is in 'prepared' state
SQLALCHEMY_ECHO = _CONFIG.getboolean("sqlalchemy", "echo")
SQLALCHEMY_ENGINE_OPTIONS = {}

LOG_LEVEL = _CONFIG.get("log", "level")
JSON_SORT_KEYS = False

CACHE_DEFAULT_TIMEOUT = 60 * 60 * 3
CACHE_THRESHOLD = 1000
CACHE_TYPE = "redis"
CACHE_REDIS_URL = f"redis://:{RedisConf.password}@{RedisConf.host}:{RedisConf.port}/{RedisConf.db2}"

