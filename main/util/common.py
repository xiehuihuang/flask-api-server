#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: common.py
# @time: 2020/9/15 16:15
# @author: jack
# @Email: 793936517@qq.com
# @desc:
import collections
import datetime
import hashlib
import logging
import time
import requests
import simplejson
from flask import jsonify, request, json
from retrying import retry

from main.util.response_code import error_map, RET

logger = logging.getLogger(__name__)


def norm_data(code, desc=None, data=None, **kwargs):
    kwargs["code"] = code if code in error_map else RET.UNKOWNERR
    kwargs["msg"] = error_map.get(code, "未知消息")
    kwargs["desc"] = desc or error_map.get(code, "未知消息")
    kwargs["data"] = data
    return kwargs


def json_resp(code, desc=None, data=None, **kwargs):
    return jsonify(norm_data(code, desc=desc, data=data, **kwargs))


class JSONEncoder(simplejson.JSONEncoder):
    def default(self, o):
        return json.JSONEncoder().default(o)


@retry(stop_max_attempt_number=2)
def parse_url(url, method="GET", raise_exception=False, timeout=10, **kwargs):
    try:
        if method.upper() in ["GET"]:
            kwargs.setdefault('allow_redirects', True)
        tt = time.time()
        resp = requests.request(method, url, timeout=timeout, **kwargs)
        logger.debug(f">>>> time:{(time.time() - tt):.3f} url: {method} {resp.url}")
        if resp.status_code != 200:
            raise Exception(resp.content.decode())
        return resp.json()
    except Exception as e:
        msg = f"地址请求失败 {method} {url} kwargs:{json.dumps(kwargs, ensure_ascii=False)} error:{e}"
        logger.error(msg)
        if raise_exception:
            raise Exception(msg)
        else:
            return {}


def request_data() -> dict:
    data = {}
    data.update(request.form)
    try:
        data.update(request.json or {})
    except Exception:
        pass

    return data


def make_cache_key(*args, **kwargs):
    ignore_field = ("timestamp", "nonce", "authorization")
    data = request_data()
    for i in ignore_field:
        if i in data:
            data.pop(i)
    request_data_byte = json.dumps(data).encode()

    args_as_sorted_tuple = tuple(sorted((pair for pair in request.args.items(multi=True))))
    args_as_bytes = str(args_as_sorted_tuple).encode()

    cache_hash = hashlib.md5()
    cache_hash.update(args_as_bytes)
    cache_hash.update(request_data_byte)
    cache_hash = str(cache_hash.hexdigest())
    cache_key = request.path + cache_hash
    return cache_key


def generate_md5(s, encoding="utf-8"):
    return str(hashlib.md5(s.encode(encoding)).hexdigest())


def get_now_time(fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.now().strftime(fmt)


def get_datetime_obj(date_str, fmt="%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.datetime.strptime(date_str, fmt)
    except:
        return False


def get_datetime_str(date_obj, fmt="%Y-%m-%d %H:%M:%S"):
    try:
        return datetime.datetime.strftime(date_obj, fmt)
    except:
        return ""


def get_timestamp(date_str, fmt="%Y-%m-%d %H:%M:%S"):
    try:
        return time.mktime(time.strptime(date_str, fmt))
    except:
        return ""
