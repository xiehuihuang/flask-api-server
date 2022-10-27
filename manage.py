#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @file: manage.py
# @time: 2020/9/15 16:21
# @author: jack
# @Email: 793936517@qq.com
# @desc:

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager

from main.setting import create_app, db

app = create_app()
manager = Manager(app)
Migrate(app, db)

manager.add_command("db", MigrateCommand)

if __name__ == '__main__':
    # db.drop_all(app=app)  # 删除数据库
    # db.create_all(app=app)  # 创建数据库
    manager.run()