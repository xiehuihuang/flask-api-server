#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: url.py
# @time: 2020/9/15 15:20
# @author: jack
# @Email: 793936517@qq.com
# @desc: 用户蓝图
from flask import Blueprint

from .view import *

blu_user = Blueprint("user", __name__)


@blu_user.route("/home", methods={"GET", "POST"})
def home():
    return "this is user home"


blu_user.add_url_rule("/login", view_func=LoginView.as_view({"POST": "login"}))            # 用户登录
blu_user.add_url_rule("/register", view_func=RegisterView.as_view({"POST": "register"}))   # 用户注册
blu_user.add_url_rule("/query", view_func=UserView.as_view({"POST": "post_query"}))        # 用户查询
blu_user.add_url_rule("/create", view_func=UserView.as_view({"POST": "create"}))           # 添加用户
blu_user.add_url_rule("/update", view_func=UserView.as_view({"PUT": "update"}))            # 更新用户
blu_user.add_url_rule("/delete", view_func=UserView.as_view({"DELETE": "delete"}))         # 删除用户