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
"""The scraper is use for website process interaction."""
from accessor.request_worker import RequestWorker
from accessor.request_crawler import RequestCrawler
from booster.aes_formatter import AESFormatter
from booster.basic_formatter import BasicFormatter
from booster.basic_parser import BasicParser
from booster.callback_formatter import CallBackFormatter
from booster.callin_parser import CallInParser
from booster.date_formatter import DateFormatter
from booster.dom_parser import DomParser
from collector.persbc_mirror import PersBCMirror


class PersBCScraper(RequestWorker):
	"""BC采集器，首页质检，用代理
    """
	
	def __init__(self):
		RequestWorker.__init__(self)
		self.RCR = RequestCrawler()  # 请求爬行器。
		self.AFR = AESFormatter()  # AES格式器。
		self.BFR = BasicFormatter()  # 基础格式器。
		self.BPR = BasicParser()  # 基础解析器。
		self.CFR = CallBackFormatter()  # 回调格式器。
		self.CPR = CallInParser(False)  # 接入解析器。
		self.DFR = DateFormatter()  # 日期格式器。
		self.DPR = DomParser()  # 文档解析器。
		self.PMR = PersBCMirror()  # BC镜像器
		# # # 返回中用到的变量
		self.order_status: str = ""  # 订单状态
		self.segments: list = []  # 航段信息
		self.passengers: list = []  # 乘客信息
	
	def init_to_assignment(self) -> bool:
		"""Assignment to logger. 赋值日志。

		Returns:
			bool
		"""
		self.RCR.logger = self.logger
		self.AFR.logger = self.logger
		self.BFR.logger = self.logger
		self.BPR.logger = self.logger
		self.CFR.logger = self.logger
		self.CPR.logger = self.logger
		self.DFR.logger = self.logger
		self.DPR.logger = self.logger
		self.PMR.logger = self.logger
		return True
	
	def process_to_main(self, process_dict: dict = None) -> dict:
		"""Main process. 主程序入口。

		Args:
			process_dict (dict): Parameters. 传参。

		Returns:
			dict
		"""
		task_id = process_dict.get("task_id")
		log_path = process_dict.get("log_path")
		source_dict = process_dict.get("source_dict")
		enable_proxy = process_dict.get("enable_proxy")
		address = process_dict.get("address")
		self.retry_count = process_dict.get("retry_count")
		if not self.retry_count:
			self.retry_count = 1
		# # # 初始化日志。
		self.init_to_logger(task_id, log_path)
		self.init_to_assignment()
		# # # 同步返回参数。
		self.callback_data = self.CFR.format_to_sync()
		# # # 解析接口参数。
		if not self.CPR.parse_to_interface(source_dict):
			self.callback_data['msg'] = "请通知技术检查接口数据参数。"
			return self.callback_data
		self.logger.info(source_dict)
		# # # 启动爬虫，建立header。
		self.RCR.set_to_session()
		self.RCR.set_to_proxy(enable_proxy, address)
		self.user_agent, self.init_header = self.RCR.build_to_header("none")
		# # # 质检流程,
		if self.process_to_index():
			if self.process_to_search():
				# if self.process_to_login():
				if self.process_to_segment():
					if self.process_to_detail():
						self.process_to_return()
						self.logger.removeHandler(self.handler)
						return self.callback_data
		# # # 错误返回。
		self.callback_data['msg'] = self.callback_msg
		# self.callback_data['msg'] = "解决问题中，请人工质检。"
		self.logger.info(self.callback_data)
		self.logger.removeHandler(self.handler)
		return self.callback_data
	
	def process_to_index(self) -> bool:
		"""首页查询航班流程
        :return:  bool
        """
		# # # 从首页进
		# self.RCR.url = "https://www.skymark.co.jp/zh_TW/"
		# self.RCR.param_data = None
		# self.RCR.header = self.BFR.format_to_same(self.init_header)
		# self.RCR.header.update({
		#     'Pragma': 'no-cache',
		#     'Cache-Control': 'no-cache',
		#     'Upgrade-Insecure-Requests': '1',
		#     'Sec-Fetch-Mode': 'navigate',
		#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
		#     'Sec-Fetch-Site': 'none',
		#     "Host": "www.skymark.co.jp",
		# })
		# if self.RCR.request_to_get():
		# https://www.res.skymark.co.jp/reserve2/?language=en&m=confirm 英文链接
		# https://www.res.skymark.co.jp/reserve2/?language=en&m=confirm
		# # # 直接请求预订查询页面
		self.RCR.url = "https://www.res.skymark.co.jp/reserve2/?language=en&m=confirm"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Upgrade-Insecure-Requests': '1',
			'Sec-Fetch-Mode': 'navigate',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'none',
		})
		if self.RCR.request_to_get():
			return True
		self.logger.info("请求预订页面超时或者错误 (*>﹏<*)【 home 】")
		self.callback_msg = "预订页面超时或者错误"
		return False
	
	def process_to_search(self) -> bool:
		"""查询详情信息流程
        :return:  bool
        """
		# 提交信息， 进行查询
		self.RCR.url = "https://www.res.skymark.co.jp/reserve2/main"
		dep_time = self.CPR.departure_time.split('-')
		pnr_number = ''
		if self.CPR.record[:2] == "00" and self.CPR.record[-2:] == "00":
			pnr_number = self.CPR.record[2:]
		else:
			pnr_number = self.CPR.record.replace('00', '')
		if not self.CPR.flight_number:
			self.callback_msg = f"航班号未找到 (*>﹏<*)【 {self.CPR.flight_number} 】"
			self.logger.info(self.callback_msg)
			return False
		self.RCR.post_data = {
			'language': 'en',
			'country': 'jp',
			'ref_currency': 'Unnecessary',
			'request': '/reserve/main.jsp',
			'fromTop': 'on',
			'year': dep_time[0],
			'month': dep_time[1],
			'day': dep_time[2],
			'flightNo': '0' + self.CPR.flight_number.replace("BC", ""),
			'reserveNo': pnr_number,
			'secondname': self.CPR.last_name,
			'firstname': self.CPR.first_name,
			'check.x': '125',
			'check.y': '47'
		}
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Origin': 'https://www.res.skymark.co.jp',
			'Upgrade-Insecure-Requests': '1',
			'Content-Type': 'application/x-www-form-urlencoded',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-User': '?1',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'same-origin',
			'Referer': 'https://www.res.skymark.co.jp/reserve2/?m=confirm&language=zh_TW',
		})
		if self.RCR.request_to_post():
			if "paymentStatus" in self.RCR.page_source:
				return True
			else:
				error, temp_list = self.DPR.parse_to_attributes(
					"text", "css", "div[id='errorTxt']", self.RCR.page_source)
				error = str(self.BPR.parse_to_replace("\r|\n|\t", "", error)).split('.')[0]
				self.callback_msg = f"订单未找到，或传入信息有误 {error}"
				self.logger.info(self.callback_msg)
				return False
		self.logger.info("获取详情页面超时或者错误 (*>﹏<*)【 detail 】")
		self.callback_msg = "获取详情页面超时或者错误"
		return False
	
	def process_to_login(self) -> bool:
		"""登录后查询航班流程
        :return:  bool
        """
		# # # 解析email页面
		self.RCR.url = "https://tickets.vueling.com/LinksHub.ashx"
		self.RCR.param_data = (
			("email", "168033518@qq.com"), ("pnr", self.CPR.record), ("event", "change"),
			("flow", "c3"), ("culture", "en-GB"),
		)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Host": "tickets.vueling.com",
			"Referer": "https://www.vueling.com/en",
			"Upgrade-Insecure-Requests": "1"
		})
		if self.RCR.request_to_get(status_code=302):
			# # # 解析跳转
			url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
			self.RCR.url = "https://tickets.vueling.com" + url
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
				"Host": "tickets.vueling.com",
				"Referer": "https://www.vueling.com/en",
				"Upgrade-Insecure-Requests": "1"
			})
			if self.RCR.request_to_get(status_code=302):
				# # # 查询错误信息
				error_message, temp_list = self.DPR.parse_to_attributes(
					"text", "css", "#validationErrorContainerReadAlongList p[role=alert]", self.RCR.page_source)
				error_message = self.BPR.parse_to_separate(error_message)
				if error_message:
					self.logger.info(f"查询订单信息错误(*>﹏<*)【{self.CPR.record}】【{error_message}】")
					self.callback_msg = f"查询订单信息错误(*>﹏<*)【{self.CPR.record}】【{error_message}】"
					return False
				# # # 解析跳转
				url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
				self.RCR.url = "https://tickets.vueling.com" + url
				self.RCR.param_data = None
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
					"Host": "tickets.vueling.com",
					"Referer": "https://www.vueling.com/en",
					"Upgrade-Insecure-Requests": "1"
				})
				if self.RCR.request_to_get():
					return True
		self.logger.info("查询超时或者错误(*>﹏<*)【query】")
		self.callback_msg = "查询超时或者错误"
		return False
	
	def process_to_segment(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		# # # 从详情页收集航段信息
		# 订单状态/付款状态
		self.order_status, temp_list = self.DPR.parse_to_attributes(
			"text", "css", 'div[id="statusLeft"] dl dd:first-of-type', self.RCR.page_source)
		if self.order_status == "Paid":
			self.order_status = "confirmed"
		# 航段信息
		segment, segment_list = self.DPR.parse_to_attributes(
			"text", "xpath", "//div[@id='resInfo']//tbody/tr[not(th)]", self.RCR.page_source)
		for i in range(1, len(segment_list) + 1):
			segment, segment_list = self.DPR.parse_to_attributes(
				"text", "xpath", f"//div[@id='resInfo']//tbody/tr[not(th)][{i}]/td//text()", self.RCR.page_source)
			# 判断票价种类
			if "Imatoku" != segment_list[6]:
				self.callback_msg = "票价种类异常 {}".format(segment_list[6])
				self.logger.info(self.callback_msg)
				return False
			# 解析时间
			flight_date = self.DFR.format_to_transform(segment_list[0], "%a %d%b%Y").strftime('%Y%m%d')
			dep_time = self.DFR.format_to_transform(segment_list[3], "%H:%M").strftime('%H%M')
			air_time = self.DFR.format_to_transform(segment_list[5], "%H:%M").strftime('%H%M')
			from_station = segment_list[2]  # 航司的名字，不是三字码，待转换
			to_station = segment_list[4]  #
			dep_code = ''  # 出发机场三字码
			arr_code = ''  # 到达机场三字码
			for c in self.PMR._country_code.items():
				if from_station in c[1]:
					dep_code = c[0]
				elif to_station in c[1]:
					arr_code = c[0]
			# 拼接参数
			self.segments.append({
				"departureAircode": dep_code,
				"arrivalAircode": arr_code,
				"flightNum": "BC" + segment_list[1],
				"departureTime": flight_date + dep_time,
				"arrivalTime": flight_date + air_time,
				"tripType": i
			})
		return True
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		passengers, passengers_list = self.DPR.parse_to_attributes(
			"text", "xpath", "//div[@id='resConf']//tbody/tr[not(th)]", self.RCR.page_source)
		for i in range(1, len(passengers_list) + 1):
			passengers, passengers_list = self.DPR.parse_to_attributes(
				"text", "xpath", f"//div[@id='resConf']//tbody/tr[not(th)][{i}]/td//text()", self.RCR.page_source)
			if 'Adult' in passengers_list[0]:  # 判断是否是成人
				passengerType = 0
			else:
				passengerType = 1
			# 姓名
			names = passengers_list[1].split('\xa0')
			self.passengers.append({
				"passengerName": f"{names[0]}/{names[1]}",
				"passengerBirthday": passengers_list[2],
				"passengerSex": passengers_list[3],
				"passengerType": passengerType,
				"passengerNationality": "",
				"identificationNumber": "",
				"cardType": "",
				"cardExpired": "",
				"service_type": "",
				"auxArray": []
			})
		return True
	
	def process_to_return(self) -> bool:
		"""Return process. 返回过程。

		Returns:
			bool
		"""
		self.callback_data["code"] = 200
		self.callback_data["success"] = "true"
		self.callback_data['msg'] = "质检成功"
		self.callback_data["ticketNumber"] = self.CPR.record
		self.callback_data["systemOrderStatus"] = self.order_status
		self.callback_data['segments'] = self.segments
		self.callback_data["passengerDataList"] = self.passengers
		self.logger.info(self.callback_data)
		return True
