#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: url.py
# @time: 2020/9/15 16:19
# @author: jack
# @Email: 793936517@qq.com
# @desc:

def register_url(app):
    """
    蓝图注册中心
    :param app:
    :return:
    """

    from main.user.url import blu_user
    app.register_blueprint(blu_user, url_prefix="/user")  # 用户模块


    print("===" * 10)
    print(app.url_map)
    print("===" * 10)
