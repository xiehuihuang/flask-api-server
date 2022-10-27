#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: wsgi.py
# @time: 2020/9/15 16:20
# @author: jack
# @Email: 793936517@qq.com
# @desc:

from main.setting import create_app, db

application = create_app()

if __name__ == '__main__':
    application.run()
