#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: model.py
# @time: 2020/9/15 15:20
# @author: jack
# @Email: 793936517@qq.com
# @desc:
import enum
from datetime import datetime

from sqlalchemy.orm import validates
from werkzeug.security import generate_password_hash, check_password_hash

from main.setting import db
from main.util.common import generate_md5
from main.util.meta import MetaModel


class UserModel(MetaModel):
    __tablename__ = "user"
    __table_args__ = {"comment": "用户"}

    id = db.Column(db.Integer, primary_key=True, doc="id")
    name = db.Column(db.String(191), unique=True, index=True, nullable=False, doc="用户名")
    password_hash = db.Column(db.String(191), nullable=False, doc="哈希密码")
    is_deleted = db.Column(db.Integer, nullable=False, default=0, doc="删除标记")
    remark = db.Column(db.Text, nullable=False, default="", doc="备注")

    def get_password(self):
        raise NotImplementedError()

    def set_password(self, value):
        self.password_hash = generate_md5(str(value))

    password = property(get_password, set_password)

    def check_password(self, password):
        return self.password_hash == generate_md5(str(password))