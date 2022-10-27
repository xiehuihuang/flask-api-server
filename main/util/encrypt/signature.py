#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: signature.py
# @time: 2020/9/15 16:10
# @author: jack
# @Email: 793936517@qq.com
# @desc: token签名生成及校验


import json
import time
import uuid
import base64
from main.config import SECRET_KEY, REQUEST_EXPIRE
from Crypto.Hash import HMAC, SHA256


def generate_sign(data, secret_key, digestmod=None, code_type="utf-8"):
    """
    生成签名
    :param data:        加签参数 例如：{"id": 1}
    :param secret_key:  密钥默认使用config.SECRET_KEY
    :param digestmod:   默认加密方法为SHA256
    :return:            加签生成的token
    """
    secret_key = secret_key or SECRET_KEY
    service = HMAC.new(secret_key.encode(code_type), digestmod=digestmod or SHA256)
    service.update(json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(code_type))
    return service.hexdigest()


def attach_sign(data, secret_key=None, sign_key="token", digestmod=None):
    """
    加签生成token, token时效为1个小时，可通过config.REQUEST_EXPIRE常量修改token时效值
    :param data:        加签参数 例如：{"id": 1}
    :param secret_key:  密钥默认使用config.SECRET_KEY
    :param sign_key:    默认为sign_key
    :param digestmod:   默认加密方法为SHA256
    :return:            加签生成的token
    """
    if sign_key in data:
        raise Exception("参数错误：数据中不能含有键sign_key")

    nonce = uuid.uuid4().hex
    if "timestamp" not in data:
        data["timestamp"] = int(time.time())
    if "nonce" not in data:
        data["nonce"] = nonce
    secret_key = secret_key or SECRET_KEY
    data_str = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    token = data_str + " " + generate_sign(data, secret_key, digestmod=digestmod)
    b64_token = base64.urlsafe_b64encode(token.encode("utf-8"))

    return b64_token.decode('utf-8')


def verify_sign(token, secret_key=None, digestmod=None, code_type="utf-8"):
    """
     token验证合法性及token时效性
    :param token: token
    :param secret_key:  密钥默认使用config.SECRET_KEY
    :param digestmod:   加密方法默认使用SHA256
    :param code_type:   默认使用utf-8
    :return: token验证成功返回 ture、否则raise返回token验证失败
    """
    try:
        token_str = base64.urlsafe_b64decode(token)
        auth = token_str.split()
        data = json.loads(auth[0])
        # if any([x not in data for x in {"timestamp", "nonce", "token"}]):
        #     raise PlusException("非法请求,参数缺失!", code=RET.REQERR)

        if int(time.time()) - int(data["timestamp"]) > REQUEST_EXPIRE:
            raise Exception(f"请求token已过期！")

        secret_key = secret_key or SECRET_KEY
        service = HMAC.new(secret_key.encode(code_type), digestmod=digestmod or SHA256)
        service.update(json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(code_type))
        service.hexverify(auth[1])
        return True
    except ValueError:
        raise Exception("token验证失败")


if __name__ == '__main__':
    id = 1                     # 用户id
    secret_key = "secret_key"  # 加签密钥、默认使用flask配置文件中config.SECRET_KEY的秘钥
    data = {
        "id": 1
    }

    token = attach_sign(data, secret_key=secret_key)
    print(f"加签生成token：{token}")

    result = verify_sign(token, secret_key)
    print(f"token权限校验结果：{result}")
