#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: setting.py
# @time: 2020/9/15 16:19
# @author: jack
# @Email: 793936517@qq.com
# @desc:

import logging
from logging.handlers import RotatingFileHandler

import simplejson
from flask import Flask, has_request_context, request, current_app, json
from flask_caching import Cache
from flask_sqlalchemy import SQLAlchemy

from main import config

db = SQLAlchemy()
cache = Cache()
dynamic_db = {}


def create_app():
    # 配置日志
    setup_log(config.LOG_LEVEL)
    # 创建Flask对象,__name__为当前目录
    app = Flask(__name__, instance_relative_config=True)
    # 加载配置
    app.config.from_object(config)
    # 初始化mysql数据库
    db.init_app(app)

    cache.init_app(app)
    cache.clear()

    from main.util.middleware import init_hook
    init_hook(app)

    class JSONEncoder(simplejson.JSONEncoder):
        def default(self, o):
            return json.JSONEncoder().default(o)

    app.json_encoder = JSONEncoder

    # 注册蓝图
    from main.url import register_url
    register_url(app)

    # 统一错误处理
    from main.util.error import exception_handler
    app.extensions["exception_handler"] = exception_handler

    return app


def setup_log(level_name):
    formatter_simple = logging.Formatter("%(levelname)-8s %(asctime)s %(filename)s:%(lineno)d %(message)s")
    formatter_long = UnwrapFormatter(
        "%(levelname)-8s %(asctime)s %(name)s %(filename)s:%(lineno)d:%(funcName)s "
        "%(request_method)s %(request_path)s %(request_addr)s %(message)s")

    handler_console = logging.StreamHandler()
    handler_console.setFormatter(formatter_simple)
    handler_console.setLevel(logging.DEBUG)

    handler_file = RotatingFileHandler("log/log.log", maxBytes=1024 * 1024 * 100, backupCount=10)
    handler_file.setFormatter(formatter_long)
    handler_file.setLevel(logging.DEBUG)

    handler_err = RotatingFileHandler("log/err.log", maxBytes=1024 * 1024 * 100, backupCount=10)
    handler_err.setFormatter(formatter_long)
    handler_err.setLevel(logging.ERROR)

    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level_name.upper()))
    logger.addHandler(handler_console)
    logger.addHandler(handler_file)
    logger.addHandler(handler_err)

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").propagate = False


class UnwrapFormatter(logging.Formatter):
    def format(self, record):
        if has_request_context():
            record.request_method = request.method.upper()
            record.request_path = request.path
            record.request_addr = request.remote_addr
        else:
            record.request_method = ""
            record.request_path = ""
            record.request_addr = ""

        s = super(UnwrapFormatter, self).format(record)
        s = s.strip().replace("\r", " ").replace("\n", " ")
        return s