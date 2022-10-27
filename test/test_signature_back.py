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
    """
    :param data: secret_id + "," + timestamp
    :param secret_key: 密钥
    hmacsha256加密
    return:加密结果转成64进制字符串形式
    """
    service = HMAC.new(secret_key.encode(code_type), digestmod=digestmod or SHA256)
    service.update(data.encode(code_type))
    return service.hexdigest()


def verify_sign(data, signature, secret_key=None, digestmod=None, code_type="utf-8"):
    """
    :param data: secret_id + "," + timestamp
    :param signature: 加签
    :param secret_key: 秘钥
    """
    # if any([x not in data for x in {"nonce"}]):
    #     raise Exception("参数缺失")

    secret_key = secret_key
    service = HMAC.new(secret_key.encode(code_type), digestmod=digestmod or SHA256)
    service.update(data.encode(code_type))
    try:
        service.hexverify(signature)
        return True
    except ValueError:
        return False


if __name__ == '__main__':
    secret_id = "admin"
    secret_key = "21232f297a57a5a743894a0e4a801fc3"
    data = secret_id + "," + str(int(time.time()))
    print(f"###########data##########：", data)
    token = generate_sign(data, secret_key)
    print(f"*********token*********", token)
    # data = secret_id + "," + str(int(time.time()))
    print(f"###########data##########：", data)

    print(verify_sign(data, token, secret_key))