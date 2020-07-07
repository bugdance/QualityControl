# -*- coding: utf-8 -*-
# =============================================================================
# Copyright (c) 2018-, pyLeo Developer. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================
"""The receiver is use for receive the data."""
# # # Import current path.
import sys

sys.path.append('..')
# # # Base package.
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import  and_, or_
from flask_apscheduler import APScheduler
from datetime import datetime
import logging
from logging import handlers
import time
import configparser
import requests
import json
# # # Packages.
from booster.callback_formatter import CallBackFormatter
from explorer.appn5j_scraper import Appn5JScraper
from explorer.corpdd_scraper import CorpDDScraper
from explorer.corpod_scraper import CorpODScraper
from explorer.corpsl_scraper import CorpSLScraper
from explorer.corptr_scraper import CorpTRScraper
from explorer.corpuo_scraper import CorpUOScraper
from explorer.pers5j_scraper import Pers5JScraper
from explorer.persak_scraper import PersAKScraper
from explorer.persbc_scraper import PersBCScraper
from explorer.persjq_scraper import PersJQScraper
from explorer.persmm_scraper import PersMMScraper
from explorer.persnk_scraper import PersNKScraper
from explorer.persqn_scraper import PersQNScraper
from explorer.perstt_scraper import PersTTScraper
from explorer.perstw_scraper import PersTWScraper
from explorer.persu2_scraper import PersU2Scraper
from explorer.persvy_scraper import PersVYScraper
from explorer.perswn_scraper import PersWNScraper
from explorer.persxw_scraper import PersXWScraper

# # # App instances. App实例。
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://quality:quality123@rm-bp171f1v1a2rht1hm0o.mysql.rds.aliyuncs.com:3306/quality?charset=utf8'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:@127.0.0.1:3306/quality?charset=utf8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# # # 日志格式化。
app.logger = logging.getLogger('flask')
app.logger.setLevel(level=logging.INFO)
app.formatter = logging.Formatter('[%(asctime)s]%(message)s')
app.handler = handlers.TimedRotatingFileHandler(
	"quality.log", when='d', backupCount=6, encoding='utf-8')
# app.handler = logging.FileHandler("quality.log")
# app.handler = logging.StreamHandler()
app.handler.setFormatter(app.formatter)
app.logger.addHandler(app.handler)


class QualityMonitor(db.Model):
    """质检数据库表"""
    __tablename__ = "quality_monitor"
    id = db.Column(db.Integer, primary_key=True)
    airline_code = db.Column(db.String(10))     # 航司二字码
    task_id = db.Column(db.String(50))          # 任务ID
    ticket_number = db.Column(db.String(50))    # 票号
    quality_time = db.Column(db.Float)          # 任务时长
    quality_success = db.Column(db.Integer)     # 是否成功
    update_time = db.Column(db.Integer)         # 更新时间
    quality_message = db.Column(db.String(250))  # 失败原因
    
    def __init__(self, airline_code, task_id, ticket_number,
                 quality_time, quality_success, update_time, quality_message):
        self.airline_code = airline_code
        self.task_id = task_id
        self.ticket_number = ticket_number
        self.quality_time = quality_time
        self.quality_success = quality_success
        self.update_time = update_time
        self.quality_message = quality_message


def quality_update(airline_code, task_id, ticket_number,
                 quality_time, quality_success, update_time, quality_message):
    """更新数据库"""
    session = db.session
    try:
        sql = "insert ignore into quality_monitor(airline_code, task_id, ticket_number, quality_time, " \
              "quality_success, update_time, quality_message) values('%s', '%s', '%s', %s, %s, %s, '%s') " \
              "on duplicate key update quality_time = %s, quality_success = %s, " \
              "update_time = %s, quality_message = '%s'" % \
              (airline_code, task_id, ticket_number, quality_time, quality_success, update_time, quality_message,
               quality_time, quality_success, update_time, quality_message)
        session.execute(sql)
        session.commit()
        session.close()
        return True
    except Exception as ex:
        app.logger.info(f"数据插入错误{ex}")
        session.close()
        return False


def service_check():
    """质检服务存活检查"""
    try:
        response = requests.post("http://192.168.0.31:8191/ServiceResponse", data={"ServiceId": 2}, timeout=5)
        app.logger.info(response.text)
    except Exception as ex:
        app.logger.info(f"质检服务请求失败{ex}")


# scheduler = APScheduler()
# scheduler.init_app(app=app)
# scheduler.add_job(func=quality_check, id='zero_time', args=[True, 86400],
#                   trigger='cron', hour=9, minute=0, next_run_time=datetime.now())
# scheduler.add_job(func=quality_check, id='one_hour', args=[False, 3600],
#                   trigger='interval', seconds=3600, next_run_time=datetime.now())
# scheduler.add_job(func=service_check, id='service_check', trigger='interval',
#                   seconds=3300, next_run_time=datetime.now())
# scheduler.start()


# # # 接口请求地址，http://x.x.x.x:18081/quality/sl/。
@app.route('/quality/<airline_company>/', methods=['POST'])
def quality_control(airline_company: str = "") -> dict:
    """支付接口。

    Args:
        airline_company (str): 航司二字码。

    Returns:
        dict
    """
    # # # 开始计时，回调声明。
    start_time = time.time()
    call_back = CallBackFormatter()
    call_back.logger = app.logger
    return_error = call_back.format_to_sync()
    # # # 解析数据并获取日志任务号。
    try:
        get_dict = json.loads(request.get_data())
        task_id = get_dict.get('orderNO')
        ticket_number = get_dict.get('ticketNumber')
        log_path = f"log/{airline_company}-{task_id}-{ticket_number}.log"
    except Exception as ex:
        msg = f"航司【{airline_company}】质检数据格式有误"
        return_error['msg'] = msg
        app.logger.info(msg)
        app.logger.info(ex)
        return jsonify(return_error)
    else:
        # # # 读取配置文件信息并配置。
        config = configparser.ConfigParser()
        config.read("config.ini", encoding="utf-8")
        # # # 读取并检查声明账户类型。
        airline_account = ""  # 账户类型。
        if 'account' in config:
            account = config.options('account')
            if airline_company.lower() in account:
                airline_account = config.get('account', airline_company.lower())
        # # # 判断账户类型是否正确。
        if airline_account in ["corp", "pers", "appn", "eapp"]:
            pass
        else:
            end_time = time.time()
            run_time = (end_time - start_time).__round__(2)
            msg = f"航司【{airline_company}】质检功能还未上线【{run_time}】【{task_id}】【{ticket_number}】"
            return_error['msg'] = msg
            app.logger.info(msg)
            quality_update(airline_company, task_id, ticket_number,
                           run_time, 0, int(end_time), "功能还未上线")
            return jsonify(return_error)
        # # # 读取并检查转发配置类型。
        forward_address = ""  # 转发地址。
        if 'forward' in config:
            forward = config.options('forward')
            if airline_company.lower() in forward:
                forward_address = config.get('forward', airline_company.lower())
        # # # 判断地址是否需要转发。
        if forward_address:
            msg = f"航司【{airline_company}】质检转发声明完成【{task_id}】【{ticket_number}】"
            app.logger.info(msg)
            try:
                request_url = f"{forward_address}/quality/{airline_company.lower()}/"
                response = requests.post(url=request_url, json=get_dict, timeout=180)
                result_data = response.json()
                result_msg = result_data.get('msg')
                success = result_data.get('success')
            except Exception as ex:
                end_time = time.time()
                run_time = (end_time - start_time).__round__(2)
                msg = f"航司【{airline_company}】质检转发地址超时【{run_time}】【{task_id}】【{ticket_number}】"
                return_error['msg'] = msg
                app.logger.info(msg)
                app.logger.info(ex)
                quality_update(airline_company, task_id, ticket_number,
                               run_time, 0, int(end_time), "转发地址超时")
                return jsonify(return_error)
            else:
                end_time = time.time()
                run_time = (end_time - start_time).__round__(2)
                msg = f"航司【{airline_company}】质检转发请求成功【{run_time}】【{task_id}】【{ticket_number}】【{result_msg}】"
                app.logger.info(msg)
                if success == "true":
                    quality_update(airline_company, task_id, ticket_number,
                                   run_time, 1, int(end_time), result_msg)
                else:
                    quality_update(airline_company, task_id, ticket_number,
                                   run_time, 0, int(end_time), result_msg)
                return jsonify(result_data)
        else:
            msg = f"航司【{airline_company}】质检本地声明完成【{task_id}】【{ticket_number}】"
            app.logger.info(msg)
            # # # 读取并检查基础配置类型。
            retry_count = ""
            if 'retry' in config:
                retry = config.options('retry')
                if airline_company.lower() in retry:
                    retry_count = config.get('retry', airline_company.lower())
            if not retry_count:
                retry_count = "1"
            # # # 读取并检查代理配置类型。
            ip_address = ""  # 代理地址。
            enable_proxy = False  # 是否需要代理。
            if 'proxy' in config:
                proxy = config.options('proxy')
                if airline_company.lower() in proxy:
                    ip_address = config.get('proxy', airline_company.lower())
            if ip_address:
                enable_proxy = True
            try:
                # # # 拼接请求参数。
                process_dict = {
                    "task_id": task_id, "log_path": log_path, "source_dict": get_dict,
                    "enable_proxy": enable_proxy, "address": ip_address, "retry_count": int(retry_count)
                }
                # # # 声明航司类。
                create_var = globals()
                scraper = create_var[airline_account.capitalize() + airline_company.upper() + "Scraper"]()
                result_data = scraper.process_to_main(process_dict)
                result_msg = result_data.get('msg')
                success = result_data.get('success')
            except Exception as ex:
                end_time = time.time()
                run_time = (end_time - start_time).__round__(2)
                msg = f"航司【{airline_company}】质检本地未知错误【{run_time}】【{task_id}】【{ticket_number}】"
                return_error['msg'] = msg
                app.logger.info(msg)
                app.logger.info(ex)
                quality_update(airline_company, task_id, ticket_number,
                               run_time, 0, int(end_time), "本地未知错误")
                return jsonify(return_error)
            else:
                end_time = time.time()
                run_time = (end_time - start_time).__round__(2)
                msg = f"航司【{airline_company}】质检本地请求成功【{run_time}】【{task_id}】【{ticket_number}】【{result_msg}】"
                app.logger.info(msg)
                if success == "true":
                    quality_update(airline_company, task_id, ticket_number,
                                   run_time, 1, int(end_time), result_msg)
                else:
                    quality_update(airline_company, task_id, ticket_number,
                                   run_time, 0, int(end_time), result_msg)
                return jsonify(result_data)


# # # 接收同步地址，http://x.x.x.x:18081/proxy/sl/。
@app.route('/proxy/<airline_company>/', methods=['POST'])
def auto_forward(airline_company: str = "") -> dict:
    """同步转发地址。

    Args:
        airline_company (str): 航司二字码。

    Returns:
        dict
    """
    # # # 定义返回格式并解析。
    return_error = {"success": "false"}
    try:
        get_dict = eval(request.get_data())
        ip_address = get_dict['ip']
    except Exception as ex:
        msg = f"航司【{airline_company}】同步转发数据有误"
        app.logger.info(msg)
        app.logger.info(ex)
        return jsonify(return_error)
    else:
        # # # 读取配置文件信息并配置。
        config = configparser.ConfigParser()
        config.read("config.ini", encoding="utf-8")
        # # # 读取并检查转发配置类型。
        if 'forward' in config:
            forward = config.options('forward')
            if airline_company.lower() in forward:
                config['forward'][airline_company.lower()] = ip_address
                config.write(open("config.ini", "w"))
                return_error['success'] = "true"
                return jsonify(return_error)
        
        msg = f"航司【{airline_company}】同步转发配置有误"
        app.logger.info(msg)
        return jsonify(return_error)


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=18081)

