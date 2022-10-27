#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: auth.py
# @time: 2020/9/15 16:11
# @author: jack
# @Email: 793936517@qq.com
# @desc:  认证和权限校验

import logging
import functools
from flask import request, g
from main.util.common import json_resp
from main.util.encrypt import verify_sign
from main.util.response_code import RET

logger = logging.getLogger(__name__)


# =================Authentication===========================
class BaseAuthentication(object):
    """权限校验
    """
    www_authenticate_realm = "token"

    @classmethod
    def authenticate(cls):
        # Authorization
        auth = request.headers.get("Authorization", "")
        auth = auth.split()
        if not auth or auth[0].lower() != cls.www_authenticate_realm:
            return None

        if len(auth) != 3:
            msg = "Invalid basic header. Credentials string wrong length."
            return json_resp(RET.PARAMERR, msg, data=None)

        return cls.authenticate_credentials(auth[1], auth[2])

    @classmethod
    def authenticate_credentials(cls, username, password):
        try:
            user = cls.get_user_info(username, password)
            cls.set_user(user)

            logger.info(f"{cls.www_authenticate_realm}认证成功,username：{user['username']}")
        except Exception as e:
            msg = f"{cls.www_authenticate_realm}认证失败，error: {e}"
            logger.info(msg)
            return json_resp(RET.AUTHERR, msg, data=None)

    @classmethod
    def get_user_info(cls, username, password):
        try:
            from main.user.model import UserModel
            user = UserModel.query.filter_by(username=username).first()
        except Exception as e:
            raise Exception(f"查询用户信息错误 {e}")
        if not user:
            raise Exception(f"用户不存在")

        if not user.check_password(password):
            raise Exception("用户名密码错误")

        if not user.is_active:
            raise Exception("User inactive or deleted.")

        return user.to_dict()

    @staticmethod
    def set_user(user):
        g.user = user


class NonceAuthentication(object):
    """服务端nonce校验
    """
    www_authenticate_realm = "nonce"

    @classmethod
    def authenticate(cls, data):
        # authorization = nonce nonce signature
        auth = data.get("authorization", "")
        auth = auth.split()
        if not auth or auth[0].lower() != cls.www_authenticate_realm:
            return None

        data.pop("authorization")

        if len(auth) != 3:
            msg = "Invalid basic header. Credentials string wrong length."
            return json_resp(RET.AUTHERR, msg, data=None)

        return cls.authenticate_credentials(auth[1], auth[2], data)

    @classmethod
    def authenticate_credentials(cls, username, signature, data):
        try:
            if not verify_sign(data, signature):
                raise Exception("签名验证失败")

        except Exception as e:
            msg = f"{cls.www_authenticate_realm}认证失败，error: {e}"
            logger.info(msg)
            return json_resp(RET.AUTHERR, msg, data=None)


class ApiAuthentication(object):
    """服务端api校验
    """
    www_authenticate_realm = "api"

    @classmethod
    def authenticate(cls, data):
        # authorization = api user signature
        auth = data.get("authorization", "")
        auth = auth.split()
        if not auth or auth[0].lower() != cls.www_authenticate_realm:
            return None

        data.pop("authorization")

        if len(auth) != 3:
            msg = "Invalid basic header. Credentials string wrong length."
            return json_resp(RET.AUTHERR, msg, data=None)

        return cls.authenticate_credentials(auth[1], auth[2], data)

    @classmethod
    def authenticate_credentials(cls, username, signature, data):
        try:
            user = cls.get_user_info(username)
            if not verify_sign(data, signature, user.password_hash):
                raise Exception("签名验证失败")

            logger.info(f"{cls.www_authenticate_realm}认证成功,username：{user.username}")
            cls.set_user(user)
        except Exception as e:
            msg = f"{cls.www_authenticate_realm}认证失败，error: {username}{e}"
            logger.info(msg)
            return json_resp(RET.AUTHERR, msg, data=None)

    @classmethod
    def get_user_info(cls, username):
        try:
            from main.user.model import UserModel
            user = UserModel.query.filter_by(username=username, is_deleted=0).first()
        except Exception as e:
            raise Exception(f"查询用户信息错误 {e}")

        if not user:
            raise Exception(f"用户不存在")

        if not user.is_active:
            raise Exception("User inactive or deleted.")

        return user.to_dict()

    @staticmethod
    def set_user(user):
        g.user = user


def login_required(view_func):
    """
    token权限校验装饰器
    """
    @functools.wraps(view_func)
    def verify_token(*args, **kwargs):
        try:
            # 在请求头上拿到token
            token = request.headers.get("token")
            if token:
                verify_sign(token)  # 校验token
            else:
                raise Exception("缺少请求参数token")

        except Exception as e:
            msg = f"check user permission error {e}"
            logger.error(msg)
            return json_resp(RET.AUTHERR, msg)

        return view_func(*args, **kwargs)

    return verify_token


def user_uri_required(f):
    """Checks whether user is logged in or raises error 401."""

    @functools.wraps(f)
    def decorator(*args, **kwargs):
        try:
            from main.user.model import UserModel, UserUriModel

            if not hasattr(g, "user"):
                raise Exception(f"用户未登录")

            if g.user.role == UserModel.RoleChoice.admin.name:
                return

            user = g.user
            request_method = request.method.upper()
            uri = request.path

            user_permission = UserUriModel.query.filter_by(
                username=user.username, request_method=request_method, uri=uri
            ).first()

            if not user_permission:
                raise Exception(f"无权限")

        except Exception as e:
            msg = f"check user permission error {e}"
            logger.error(msg)
            return json_resp(RET.AUTHERR, msg)

        return f(*args, **kwargs)

    return decorator


class ApiUserPermission:
    def __init__(self):
        self.headers = {}

    def check_permission(self):
        try:
            from main.user.model import UserModel, UserUriModel

            if not hasattr(g, "user"):
                raise Exception(f"用户未登录")

            if g.user.role == UserModel.RoleChoice.admin.name:
                return

            user = g.user
            request_method = request.method.upper()
            uri = request.path

            user_permission = UserUriModel.query.filter_by(
                username=user.username, request_method=request_method, uri=uri
            ).first()

            if not user_permission:
                raise Exception(f"无权限")

        except Exception as e:
            msg = f"check user permission error {e}"
            logger.error(msg)
            return json_resp(RET.AUTHERR, msg)

    def __call__(self, f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            permission = self.check_permission()
            if permission:
                return permission
            return f(*args, **kwargs)

        return wrapped


class AdminPermission:
    def __init__(self):
        self.headers = {}

    def check_permission(self):
        try:
            from main.user.model import UserModel, UserUriModel

            if not hasattr(g, "user"):
                raise Exception(f"用户未登录")

            if g.user.role != UserModel.RoleChoice.admin.name:
                raise Exception(f"无权限")

        except Exception as e:
            msg = f"check user permission error {e}"
            logger.error(msg)
            return json_resp(RET.AUTHERR, msg)

    def __call__(self, f):
        def wrapped(*args, **kwargs):
            permission = self.check_permission()
            if permission:
                return permission
            return f(*args, **kwargs)

        return wrapped

