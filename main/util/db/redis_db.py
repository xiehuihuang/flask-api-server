#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: redis_db.py
# @time: 2020/9/15 16:09
# @author: jack
# @Email: 793936517@qq.com
# @desc:


import logging

import redis

from main import config

logger = logging.getLogger(__name__)


class Redis(object):
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=True, long=False, **kwargs):
        self.__kw = dict(host=host, port=port, db=db, decode_responses=decode_responses, **kwargs)
        self.long = long
        if self.long:
            connection_pool = redis.ConnectionPool(**self.__kw)
            self.__long_conn = redis.Redis(connection_pool=connection_pool)

    @property
    def __conn(self):
        if self.long:
            return self.__long_conn
        return redis.Redis(**self.__kw)

    def __getattr__(self, item):
        def _(*args, **kwargs):
            try:
                return getattr(self.__conn, item)(*args, **kwargs)
            except Exception as e:
                logger.error(f"redis操作失败 {e}")

        return _


redis_store = Redis(host=config.RedisConf.host,
                    port=config.RedisConf.port,
                    db=config.RedisConf.db1,
                    password=config.RedisConf.password,
                    long=True)  # type: redis.Redis


def redis_conn(db=None) -> redis.Redis:
    return Redis(host=config.RedisConf.host, port=config.RedisConf.port, db=db or config.RedisConf.db1,
                 password=config.RedisConf.password)