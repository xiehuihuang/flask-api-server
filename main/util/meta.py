#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: meta.py
# @time: 2020/9/15 16:13
# @author: jack
# @Email: 793936517@qq.com
# @desc:  基础类：基础模型，自定义模型字段，基础视图
import logging
import uuid
from datetime import datetime

from flask import request, g

from main.setting import db
from main.util.common import request_data
from main.util.mixin import RawQueryHandle, BaseViewMixin, GraphicsDataHandle
from main.util.error import HttpResponseError

logger = logging.getLogger(__name__)


class DataDict(dict):
    def __getattr__(self, item):
        return self.get(item, None)


class MetaModel(db.Model):
    __abstract__ = True

    def create(self, params={}):
        try:
            for k, v in params.items():
                if hasattr(self, k):
                    setattr(self, k, v)

            db.session.add(self)
            db.session.commit()
            return self.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e

    def update(self, params={}):
        try:
            for k, v in params.items():
                if hasattr(self, k):
                    setattr(self, k, v)

            db.session.commit()
            return self.to_dict()
        except Exception as e:
            db.session.rollback()
            raise e

    def to_dict(self):
        return DataDict({x.name: getattr(self, x.name, None) for x in self.__table__.columns})

    @staticmethod
    def to_list(obj_list):
        ret = []
        for i in obj_list:
            ret.append(i.to_dict())

        return ret


class RichBaseModel(MetaModel):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, doc="id")
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.now, doc="创建时间")
    update_time = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, doc="更新时间")
    author = db.Column(db.String(191), nullable=False, doc="变更人")
    is_deleted = db.Column(db.Integer, nullable=False, default=0, doc="删除标记")
    remark = db.Column(db.Text, nullable=False, default="", doc="备注")

    def to_dict(self):
        ignore = ("create_time", "update_time")
        ret = DataDict({x.name: getattr(self, x.name, None) for x in self.__table__.columns if x.name not in ignore})
        ret["create_time"] = self.create_time.strftime("%Y-%m-%d %H:%M:%S")
        ret["update_time"] = self.update_time.strftime("%Y-%m-%d %H:%M:%S")
        return ret


class MetaView(object):
    http_method_funcs = frozenset(
        ["GET", "POST", "HEAD", "OPTIONS", "DELETE", "PUT", "TRACE", "PATCH"]
    )
    methods = set()
    provide_automatic_options = None
    decorators = ()
    model = None

    @classmethod
    def as_view(cls, actions, *class_args, **class_kwargs):
        """ this refer flask MethodView and django rest framework ViewSetMixin
        For example:
        actions = {
            "get":"get_func",
            "post":"post_func",
        }
        """

        if not actions or not isinstance(actions, dict):
            raise TypeError("The `actions` argument must be provided when "
                            "calling `.as_view()` on a ViewSet. For example "
                            "`.as_view({'get': 'list'})`")

        cls.methods = set([x.upper() for x in actions])

        def view(*args, **kwargs):
            self = cls(*class_args, **class_kwargs)

            for method, action in actions.items():
                handler = getattr(self, action)
                setattr(self, method.upper(), handler)

            if hasattr(self, "GET") and not hasattr(self, "HEAD"):
                self.HEAD = self.GET

            self.args = args
            self.kwargs = kwargs
            return self.dispatch_request(*args, **kwargs)

        # We attach the view class to the view function for two reasons:
        # first of all it allows us to easily figure out what class-based
        # view this thing came from, secondly it's also used for instantiating
        # the view class so you can actually replace it with something else
        # for testing purposes and debugging.
        view.cls = cls
        view.__name__ = uuid.uuid4().hex
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        # update_wrapper(view, cls, updated=())
        view.methods = cls.methods
        view.provide_automatic_options = cls.provide_automatic_options

        return cls.initial(view)

    @classmethod
    def initial(cls, view):
        try:
            if cls.decorators:
                for decorator in cls.decorators:
                    view = decorator(view)
            return view
        except Exception as exc:
            return cls.handle_exception(exc)

    def http_method_not_allowed(self, *args, **kwargs):
        # return MethodNotAllowed()
        ms = f"the {request.method} method miss!"
        logger.error(ms)
        return HttpResponseError.method_error(ms)

    @classmethod
    def handle_exception(cls, exc):
        ms = f"{cls.__name__} {request.path} {exc}"
        logger.error(ms)
        return HttpResponseError.server_error(ms)

    def dispatch_request(self, *args, **kwargs):
        try:
            if request.method.upper() in self.http_method_funcs:
                handler = getattr(self, request.method.upper(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = handler(*args, **kwargs)
        except Exception as exc:
            response = self.handle_exception(exc)

        return response

    @property
    def request_args(self):
        return request.args

    @property
    def request_data(self):
        return request_data()

    @property
    def current_user(self):
        if hasattr(g, "user"):
            return g.user
        return DataDict({
            "id": None,
            "username": request.headers.get("host"),
            "nickname": None,
            "password_hash": None,
            "role": None,
        })

    @staticmethod
    def db_commit():
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e


class MetaViewSet(MetaView, RawQueryHandle, BaseViewMixin, GraphicsDataHandle):
    decorators = ()
    resources = ""
    query_field = ()
    create_field = ()
    update_field = ()
    create_required_field = ()
    update_required_field = ("id",)