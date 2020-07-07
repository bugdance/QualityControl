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
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Text, create_engine
from sqlalchemy import and_, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import time
import logging
import requests

# # # 日志格式化。
logger = logging.getLogger("flask")
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('[%(asctime)s]%(message)s')
handler = logging.FileHandler("count.log")
# handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
# # # 数据库。
engine = create_engine('mysql://quality:quality123@rm-bp171f1v1a2rht1hm0o.mysql.rds.aliyuncs.com:3306/quality?charset'
                       '=utf8')
# engine = create_engine('mysql://root:@127.0.0.1:3306/quality?charset=utf8')
DBSession = sessionmaker(bind=engine)
Model = declarative_base()


class QualityMonitor(Model):
	"""质检数据库表"""
	__tablename__ = "quality_monitor"
	id = Column(Integer, primary_key=True)
	airline_code = Column(String(10))  # 航司二字码
	task_id = Column(String(50))  # 任务ID
	ticket_number = Column(String(50))  # 票号
	quality_time = Column(Float)  # 任务时长
	quality_success = Column(Integer)  # 是否成功
	update_time = Column(Integer)  # 更新时间
	quality_message = Column(String(250))  # 失败原因
	
	def __init__(self, airline_code, task_id, ticket_number,
	             quality_time, quality_success, update_time, quality_message):
		self.airline_code = airline_code
		self.task_id = task_id
		self.ticket_number = ticket_number
		self.quality_time = quality_time
		self.quality_success = quality_success
		self.update_time = update_time
		self.quality_message = quality_message


def quality_check(is_zero: bool = False, time_interval: int = 86400):
	"""检查数据库，提醒格式markdown,每行不超过10字。"""
	session = DBSession()
	try:
		# # # 获取当前时间戳，和相差时间戳
		now_time = int(time.time())
		last_time = now_time - time_interval
		hour = (time_interval / 3600).__round__(2)
		if is_zero:
			# # # 获取当天零点时间戳
			now = datetime.now()
			now_zero = datetime.now().replace(
				year=now.year, month=now.month, day=now.day, hour=0, minute=0, second=0)
			last_time = int(time.mktime(now_zero.timetuple()))
		# # # 钉钉预警内容标题
		content = ""
		# # # 获取总数
		sum_count = session.query(QualityMonitor).filter(
			QualityMonitor.update_time > last_time,
			QualityMonitor.update_time < now_time
		).count()
		# # # 判断有没有数据。
		if not sum_count:
			if is_zero:
				content += f"\n ### 零点至目前前端总数(*0*)"
			else:
				content += f"\n ### {hour}小时内前端总数(*0*)"
		else:
			if is_zero:
				content += f"\n ### 零点至目前前端总数(*{sum_count}*)"
			else:
				content += f"\n ### {hour}小时内前端总数(*{sum_count}*)"
			# # # 轮循查每个失败词失败率
			words = ["失败", "超时", "错误"]
			rule = or_(*[QualityMonitor.quality_message.like(f"%{w}%") for w in words])
			content += f"\n - **统计关键词: 失败,超时,错误**"
			# # # 轮循查每个航司失败率
			fail_sum = 0
			over_sum = 0
			company = [
				"5j", "dd", "od", "sl", "tr", "uo", "ak", "ak-acc",
				"bc", "jq", "mm", "nk", "qn", "tt", "tw", "u2",
				"vj-acc", "vy", "wn", "xw"
			]
			content += f"\n ### 航司-(超时/失败/总数)-失败率:"
			for i in company:
				sum_company = session.query(QualityMonitor).filter(
					QualityMonitor.airline_code == i,
					QualityMonitor.update_time > last_time,
					QualityMonitor.update_time < now_time
				).count()
				if not sum_company:
					continue
				else:
					timeout = 60
					if i == "5j" or i == "vj-acc":
						timeout = 100
					# # # 判断有没有超时的。
					overtime_company = session.query(QualityMonitor).filter(
						QualityMonitor.airline_code == i,
						QualityMonitor.quality_time >= timeout,
						QualityMonitor.update_time > last_time,
						QualityMonitor.update_time < now_time
					).count()
					if not overtime_company:
						overtime_company = 0
					# # # 查询失败个数
					failure_company = session.query(QualityMonitor).filter(
						QualityMonitor.airline_code == i,
						QualityMonitor.quality_time < timeout,
						rule,
						QualityMonitor.update_time > last_time,
						QualityMonitor.update_time < now_time
					).count()
					if not failure_company:
						failure_company = 0
					# # # 判断失败率。
					if not overtime_company and not failure_company:
						content += f"\n - **{i.upper()}**  (**0/0/{sum_company}**)"
					else:
						fail_sum += failure_company
						over_sum += overtime_company
						fail = overtime_company + failure_company
						rate = ((fail / sum_company) * 100).__round__(2)
						content += f"\n - **{i.upper()}**  " \
						           f"(**{overtime_company}/{failure_company}/{sum_company}**)--" \
						           f"*{rate}%*"
			# # # 总的成功率。
			fail_count = over_sum + fail_sum
			if not fail_count:
				content += f"\n ### 恭喜你成功率满分(-__- )y--～"
			else:
				rate = ((fail_count / sum_count) * 100).__round__(2)
				content += f"\n ### 前端总计-(**{over_sum}/{fail_sum}/{sum_count}**)-*{rate}%*"
		
		# # # 钉钉提醒程序
		url = "https://oapi.dingtalk.com/robot/send?access_token=" \
		      "c335e8d7e63920510c242d8fe1a17ceff56e47b49a956a76bcc78442565b69c5"
		headers = {'Content-Type': 'application/json'}
		json_text = {
			"msgtype": "markdown",
			"markdown": {
				"title": "质检钉钉提醒测试",
				"text": content
			}
		}
		response = requests.post(url, json=json_text, headers=headers)
		logger.info(response.text)
		session.close()
		return True
	except Exception as ex:
		logger.info(f"质检检查服务请求失败{ex}")
		session.close()
		return False


scheduler = BlockingScheduler()
scheduler.add_job(func=quality_check, id='zero_time', args=[True, 86400],
                  trigger='cron', hour=9, minute=0, next_run_time=datetime.now())
scheduler.add_job(func=quality_check, id='one_hour', args=[False, 3600],
                  trigger='interval', seconds=3600, next_run_time=datetime.now())
scheduler.start()