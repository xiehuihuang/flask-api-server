#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: middleware.py
# @time: 2020/9/15 16:14
# @author: jack
# @Email: 793936517@qq.com
# @desc:
import logging
from main.util.common import json_resp
from main.util.response_code import RET

logger = logging.getLogger(__name__)


def authentication():
    try:
        from main.util.auth import ApiAuthentication
        from main.util.auth import WebAuthentication
        return WebAuthentication() or ApiAuthentication()

    except Exception as e:
        msg = f"认证失败：{e}"
        logger.error(msg)
        return json_resp(getattr(e, "code", RET.AUTHERR), msg)


def init_hook(app):
    """Flask 请求钩子(hook)
    """

    @app.before_first_request
    def handle_before_first_request():
        """在第一次请求处理之前被执行 (服务器启动后,只会执行一次)
        """
        pass

    @app.before_request
    def handle_before_request():
        """在每次请求之前都被执行
        """
        pass
        # return authentication()

    @app.after_request
    def handle_after_request(response):
        """
        # 必须传入response参数(视图函数返回的response)
        在每次请求(视图函数处理)之后都被执行, 前提是视图函数没有出现异常
        """
        return response

    @app.teardown_request
    def handle_teardown_request(response):
        """
         # 必须传入response参数(视图函数返回的response)
        在每次请求(视图函数处理)之后都被执行，无论视图函数是否出现异常都被执行(只有在生产环境下才会执行)
        """
        return response
