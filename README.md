# flask-api-server
flask Api接口服务基础框架Demo （用户注册、登录、用户查询、修改密码、token鉴权）

#### 一、开发环境安装：
1.1 项目开发工具及使用技术栈
  + python: 3.8.10
  + 开发工具：pyCharm2021.3.3
  + 技术栈 python、flask、SQLAlchemy、systemctl + uwsgi
  + 数据库：mysql8、redis4.0

1.2 代码git clone
  + git clone仓库代码：git clone git@github.com:xiehuihuang/flask-api-server.git

1.3 创建venv虚拟环境后，再安装项目依赖包
``` shell
  pip install -r requirement.txt -i https://pypi.douban.com/simple
```
1.4 mysql文件详见flask_api_server/doc/api_server_data.sql

1.5 项目conf/config.ini配置文件修改
   + git clone代码conf文件夹中有config_temp.ini，拷贝一份重命名为config.ini
   + 修改config.ini配置文件中mysql、redis连接配置

1.6 接口文档附件详见doc/api-server.postman_collection.json可直接导入postman中

##### 二、用户模块（user）：  
1 用户Api接口 
  + 注册
  + 登录成功生成token
  + 用户列表查询 （token鉴权）
  + 添加用户    （token鉴权）
  + 更新用户    （token鉴权）
  + 删除用户    （token鉴权）

2 框架基础模块
  + 日志记录格式处理
  + 统一错误处理
  + orm查询封装详见BaseViewMixin
  + sql语句查询封装详见RawQueryHandle，可支持panadas
  + api接口响应状态码map映射详见response_code.py
  + token鉴权调用装饰器@login_required

3 阿里云Linux服务器上基于venv虚拟环境：Flask + uwsgi + Systemctl 服务部署与配置
  + 1.创建flask-api-server.service服务管理脚本，具体如下
  ``` shell
  打开目录
  $ cd /etc/systemd/system/
  # 后缀名必须 .service
  $ vim flask-api-server.service
  # 复制如下代码到 flask-api-server.service 到改文件保存且退出(:wq)
  ``` 
  ``` text
  [Unit]
  # 描述
  # /usr/lib/systemd/system
  Description= flask-api-server service daemon
  After=network.target
   
  [Service]
  # 服务启动的命令
  WorkingDirectory = /app/flask-api-server
  ExecStart=/app/flask-api-server/venv/bin/uwsgi --die-on-term --env SERVER_ENV=produce --ini /app/flask-api-server/conf/uwsgi.ini
  ExecReload=/bin/kill -HUP $MAINPID
  KillMode=control-group
  Restart=on-failure
  RestartSec=15s
  ```
   
  + 2.启动 flask-api-server 项目服务
    + 重新加载所有服务配置，如下命令:
    ``` shell
    # 只要有.service 服务配置更新, 必须执行改命令才会生效
    $ systemctl daemon-reload
    ``` 
    + 启动服务、赞同服务、重启服务、查看服务运行状态
      ``` shell
      # 服务状态或者查看日志等
      $ sudo systemctl status flask-api-server.service
      # 暂停服务
      $ sudo systemctl stop flask-api-server.service
      # 启动服务
      $ sudo systemctl start flask-api-server.service
      # 重启服务
      $ sudo systemctl restart flask-api-server.service

      ``` 
