#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: __init__.py.py
# @time: 2020/9/15 15:21
# @author: jack
# @Email: 793936517@qq.com
# @desc:  redis数据连接封装

__all__ = [
    'redis_store', 'redis_conn'
    ]

from main.util.db.redis_db import redis_store, redis_conn
