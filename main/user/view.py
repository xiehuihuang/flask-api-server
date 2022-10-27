#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: view.py
# @time: 2020/9/15 15:20
# @author: jack
# @Email: 793936517@qq.com
# @desc:
import logging
import time
from .model import *
from main.util.meta import MetaViewSet
from main.util.common import json_resp, make_cache_key, generate_md5
from main.util.encrypt import attach_sign
from main.util.response_code import RET
from main.util.auth import login_required
from main.util.error import PlusException

logger = logging.getLogger(__name__)


class LoginView(MetaViewSet):
    resources = "用户登录"
    model = UserModel
    query_field = (
        "name",
        "password",
    )
    required_field = (
        "name",
        "password",
    )

    @property
    def queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def login(self):
        try:
            logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
            params = {x: self.request_data.get(x) for x in self.query_field if self.request_data.get(x, "") != ""}
            if not all([x in params for x in self.required_field]):
                raise PlusException("缺少必填参数")

            password_hash = generate_md5(params.get("password"))
            params.pop("password")
            params.update({"password_hash": password_hash})
            instance = self.queryset.filter_by(**params).first()
            if not instance:
                raise PlusException(f"账号或密码错误", code=RET.NODATA)

            data = {
                "id": instance.id
            }
            result = {
                "token": attach_sign(data)
            }

            return json_resp(RET.OK, f"{self.resources}成功", data=result)

        except Exception as e:
            logger.error(f"{self.resources}错误 params:{self.request_data} error:{e}")
            return json_resp(getattr(e, "code", RET.SERVERERR), f"{self.resources}错误 error:{e}", data=None)


class RegisterView(MetaViewSet):
    resources = "用户注册"
    model = UserModel
    query_field = (
        "name",
        "password",
    )
    required_field = (
        "name",
        "password",
    )

    @property
    def queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def register(self):
        try:
            logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
            params = {x: self.request_data.get(x) for x in self.query_field if self.request_data.get(x, "") != ""}

            if not all([x in params for x in self.required_field]):
                raise PlusException("缺少必填参数")

            instance = self.queryset.filter_by(name=params['name']).first()
            if instance:
                raise PlusException(f"用户已存在", code=RET.DATAEXIST)

            obj = self.model(**params)
            data = obj.create()

            return json_resp(RET.OK, f"{self.resources}成功", data=data)

        except Exception as e:
            logger.error(f"{self.resources}错误 params:{self.request_data} error:{e}")
            return json_resp(getattr(e, "code", RET.SERVERERR), f"{self.resources}错误 error:{e}", data=None)


class UserView(MetaViewSet):
    resources = "用户信息"
    model = UserModel
    query_field = (
        "id",
        "name",
        "remark",
    )
    create_field = (
        "name",
        "password",
        "remark",
    )
    update_field = (
        "id",
        "name",
        "password",
        "remark",
    )
    create_required_field = (
        "name",
        "password",
    )

    @property
    def queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    @login_required
    def post_query(self):
        try:
            logger.info(f"{self.resources}查询 user:{self.current_user.username} params:{self.request_data}")
            params = {x: self.request_data.get(x) for x in self.query_field if self.request_data.get(x, "") != ""}

            queryset = self.queryset.filter_by(**params)
            offset = self.request_data.get("offset")
            limit = self.request_data.get("limit")
            if offset and limit:
                instance = queryset.offset((int(offset) - 1) * int(limit)).limit(int(limit)).all()
                total = queryset.count()
            else:
                instance = queryset.all()
                total = len(instance)

            data = self.model.to_list(instance)
            return json_resp(RET.OK, f"{self.resources}查询成功", data=data, total=total)
        except Exception as e:
            logger.error(f"{self.resources}查询错误 params:{self.request_data} error:{e}")
            return json_resp(getattr(e, "code", RET.SERVERERR), f"{self.resources}查询错误 error:{e}", data=None)

    @login_required
    def create(self):
        try:
            logger.info(f"{self.resources}创建 user:{self.current_user.username} params:{self.request_data}")
            params = {x: self.request_data.get(x) for x in self.create_field if self.request_data.get(x) is not None}

            if not all([x in params for x in self.create_required_field]):
                raise PlusException(f"缺少必填参数")

            obj = self.model(**params)
            obj.password = params["password"]
            data = obj.create()

            return json_resp(RET.OK, f"{self.resources}创建成功", data=data)
        except Exception as e:
            logger.error(f"{self.resources}创建错误 params:{self.request_data} error:{e}")
            return json_resp(getattr(e, "code", RET.SERVERERR), f"{self.resources}创建错误 error:{e}", data=None)

    @property
    def update_queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    @login_required
    def update(self):
        try:
            logger.info(f"{self.resources}更新 user:{self.current_user.username} params:{self.request_data}")
            params = {x: self.request_data.get(x) for x in self.update_field if self.request_data.get(x) is not None}

            if not all([x in params for x in self.update_required_field]):
                raise PlusException("缺少必填参数")
            pk = params.pop("id")

            instance = self.update_queryset.filter_by(id=pk).first()
            if not instance:
                raise PlusException(f"对象不存在", code=RET.NODATA)
            for k, v in params.items():
                setattr(instance, k, v)

            result = instance.update()

            return json_resp(RET.OK, f"{self.resources}更新成功", data=result)
        except Exception as e:
            logger.error(f"{self.resources}更新错误 params:{self.request_data} error:{e}")
            return json_resp(getattr(e, "code", RET.SERVERERR), f"{self.resources}更新错误 error:{e}", data=None)

    @property
    def delete_queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    @login_required
    def delete(self):
        try:
            logger.info(f"{self.resources}删除 user:{self.current_user.username} params:{self.request_data}")

            pk = self.request_data.get("id")
            is_deleted = self.request_data.get("is_deleted", True)
            if pk is None:
                raise PlusException("缺少id参数")

            result = self.delete_queryset.filter_by(id=pk).update(dict(
                author=self.current_user.username,
                is_deleted=self.model.id if is_deleted else 0
            ))
            self.db_commit()

            return json_resp(RET.OK, f"{self.resources}删除成功", data=result)
        except Exception as e:
            logger.error(f"{self.resources}删除错误 params:{self.request_data} error:{e}")
            return json_resp(getattr(e, "code", RET.SERVERERR), f"{self.resources}删除错误 error:{e}", data=None)

