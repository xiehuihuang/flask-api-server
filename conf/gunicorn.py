#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @File   : gunicorn.py
# @Time   : 2020/9/15 14:41
# @Desc   :

# 并行工作进程数
workers = 4

# 指定每个工作者的线程数
threads = 2

# 端口 5000
bind = '0.0.0.0:5000'

# 设置守护进程,将进程交给supervisor管理
daemon = 'false'

# 工作模式协程
worker_class = 'gevent'

# 设置最大并发量
worker_connections = 2000

# 设置进程文件目录
pidfile = '/var/run/gunicorn.pid'

# 设置gunicorn访问日志格式，错误日志无法设置
access_log_format = '%(t)s %(p)s %(h)s "%(r)s" %(s)s %(L)s %(b)s %(f)s" "%(a)s"'
accesslog = "log/gunicorn_acc.log"

errorlog = "log/gunicorn_err.log"

loglevel = "info"

# 切换工作目录
# chdir = '/app/api-server'
