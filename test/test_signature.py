#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: test_signature.py
# @time: 2020/9/5 16:39
# @author: jack
# @Email: 793936517@qq.com
# @desc:


import json
import time
import uuid
from Crypto.Hash import HMAC, SHA256


def generate_sign(data, secret_key, digestmod=None, code_type="utf-8"):

    service = HMAC.new(secret_key.encode(code_type), digestmod=digestmod or SHA256)
    service.update(json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(code_type))
    return service.hexdigest()


def attach_sign(data, secret_key=None, sign_key="authorization", prefix="", digestmod=None):
    if sign_key in data:
        raise Exception("参数错误：数据中不能含有键sign_key")

    nonce = uuid.uuid4().hex
    if "timestamp" not in data:
        data["timestamp"] = int(time.time())
    if "nonce" not in data:
        data["nonce"] = nonce
    secret_key = secret_key or nonce
    data[sign_key] = prefix + generate_sign(data, secret_key, digestmod=digestmod)
    return data


def verify_sign(data, signature, secret_key=None, digestmod=None, code_type="utf-8"):
    if any([x not in data for x in {"nonce"}]):
        raise Exception("参数缺失")

    secret_key = secret_key or data["nonce"]
    service = HMAC.new(secret_key.encode(code_type), digestmod=digestmod or SHA256)
    service.update(json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(code_type))
    try:
        service.hexverify(signature)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    secret_id = "admin"
    secret_key = "21232f297a57a5a743894a0e4a801fc3"
    data = {
        "name": "jack",
        "mobile": "13512345678"
    }

    data = attach_sign(data, secret_key=secret_key, prefix=f"api {secret_id} ")
    print(json.dumps(data, ensure_ascii=False, indent=2))

    auth = data.pop("authorization")
    auth = auth.split()
    print(verify_sign(data, auth[2], secret_key))