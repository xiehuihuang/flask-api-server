#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: mixin.py
# @time: 2020/9/15 16:14
# @author: jack
# @Email: 793936517@qq.com
# @desc:
import collections
import logging
import re

from flask import request
from sqlalchemy import text, cast

from decimal import Decimal
from main.setting import db
from main.util.common import json_resp
from main.util.error import PlusException
from main.util.response_code import RET

logger = logging.getLogger(__name__)


class RawQueryHandle:
    @staticmethod
    def raw_params_to_filter(params):
        re_escape = re.compile(r"([\\'])")
        return " and ".join([f"{k}='" + re_escape.sub(r'\\\1', v) + "'" for k, v in params.items()]) or "1=1"

    @staticmethod
    def raw_get_sql_count(sql):
        query = db.session.execute(sql)
        return query.rowcount()

    @staticmethod
    def raw_get_sql_keys(sql):
        query = db.session.execute(sql)
        return query.keys()

    @staticmethod
    def raw_queryset_to_dict(queryset, default=None):
        if not queryset:
            return {}
        row = queryset.items()
        return {x[0]: x[1] if x[1] is not None else default for x in row}

    @classmethod
    def raw_queryset_list_to_dict_list(cls, queryset, default=None):
        return [cls.raw_queryset_to_dict(x, default) for x in queryset]

    @staticmethod
    def raw_get_sql_fetchone(sql, must=True, default=None):
        query = db.session.execute(text(sql))
        queryset = query.fetchone()
        if not queryset:
            if must:
                return {x: default for x in query.keys()}
            return {}
        row = queryset.items()
        return {x[0]: x[1] if x[1] is not None else default for x in row}

    @staticmethod
    def raw_get_sql_fetchall(sql, default=None):
        queryset = db.session.execute(text(sql)).fetchall()
        ret = []
        for row in queryset:
            content = row.items()
            ret.append({x[0]: x[1] if x[1] is not None else default for x in content})
        return ret


class BaseViewMixin:
    like_field = []

    @property
    def queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def perform_query(self, queryset, params):
        like_field = self.like_field
        return queryset.filter_by(**{x: params[x] for x in params if x not in like_field}).filter(
            *[cast(getattr(self.model, x), db.String).like(f"%{params[x]}%") for x in params
              if hasattr(self.model, x) and x in like_field])

    def post_query(self):
        self.resources += "查询"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
        params = {x: self.request_data.get(x) for x in self.query_field if self.request_data.get(x, "") != ""}

        queryset = self.perform_query(self.queryset, params)
        queryset = queryset.order_by(self.model.id.desc())
        offset = self.request_data.get("offset")
        limit = self.request_data.get("limit")
        if offset and limit:
            instance = queryset.offset((int(offset) - 1) * int(limit)).limit(int(limit)).all()
            total = queryset.count()
        else:
            instance = queryset.all()
            total = len(instance)

        data = self.model.to_list(instance)
        return json_resp(RET.OK, f"{self.resources}成功", data=data, total=total)

    def create(self):
        self.resources += "创建"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
        params = {x: self.request_data.get(x) for x in self.create_field if self.request_data.get(x) is not None}

        if not all([x in params for x in self.create_required_field]):
            raise PlusException(f"缺少必填参数")

        params["author"] = self.current_user.username
        obj = self.model(**params)
        data = obj.create()

        return json_resp(RET.OK, f"{self.resources}成功", data=data)

    @property
    def update_queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def update(self):
        self.resources += "更新"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")
        params = {x: self.request_data.get(x) for x in self.update_field if self.request_data.get(x) is not None}

        if not all([x in params for x in self.update_required_field]):
            raise PlusException("缺少必填参数")
        pk = params.pop("id")

        params["author"] = self.current_user.username
        result = self.update_queryset.filter_by(id=pk).update(params)
        self.db_commit()

        return json_resp(RET.OK, f"{self.resources}成功", data=result)

    @property
    def delete_queryset(self):
        return self.model.query.filter_by(is_deleted=0)

    def abs_delete(self):
        self.resources += "物理删除"
        logger.info(f"{self.resources} user:{self.current_user.username} params:{self.request_data}")

        pk = self.request_data.get("id")
        if pk is None:
            raise PlusException("缺少id参数")

        result = self.delete_queryset.filter_by(id=pk).delete()
        self.db_commit()

        return json_resp(RET.OK, f"{self.resources}成功", data=result)