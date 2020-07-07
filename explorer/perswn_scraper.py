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


class PersWNScraper(RequestWorker):
	"""WN采集器，首页质检，用代理
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
		# # # 质检流程, 判断走不走企业账户
		# if self.CPR.username == "168033518@qq.com":
		if self.process_to_index():
			if self.process_to_search():
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
		# # # 请求首页
		self.RCR.url = "https://www.southwest.com/air/manage-reservation/index.html"
		self.RCR.param_data = (
			('redirectToVision', 'true'),
			('leapfrogRequest', 'true'),
		)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'none',
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Upgrade-Insecure-Requests': '1',
			'Sec-Fetch-Mode': 'navigate',
			'Host': 'www.southwest.com'
		})
		if self.RCR.request_to_get():
			return True
		self.logger.info("首页超时或者错误(*>﹏<*)【home】")
		self.callback_msg = "首页超时或者错误"
		return False
	
	def process_to_search(self) -> bool:
		"""查询详情信息流程
        :return:  bool
        """
		# 提交票号，姓名信息
		self.RCR.url = "https://www.southwest.com/api/air-misc/v1/air-misc/page/air/manage-reservation/view"
		data = {
			"confirmationNumber": self.CPR.record,
			"passengerFirstName": self.CPR.first_name,
			"passengerLastName": self.CPR.last_name,
			"application": "air-manage-reservation",
			"site": "southwest"
		}
		self.RCR.post_data = str(data).replace('\'', '\"')
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Sec-Fetch-Mode': 'cors',
			'Origin': 'https://www.southwest.com',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh-CN,zh;q=0.9',
			'Authorization': 'null null',
			'X-Api-IDToken': 'null',
			'X-Channel-ID': 'southwest',
			'Pragma': 'no-cache',
			'Content-Type': 'application/json',
			'Accept': 'application/json, text/javascript, */*; q=0.01',
			'Cache-Control': 'no-cache',
			'Referer': 'https://www.southwest.com/air/manage-reservation/index.html?redirectToVision=true&leapfrogRequest=true',
			'Sec-Fetch-Site': 'same-origin',
			'X-API-Key': 'l7xx944d175ea25f4b9c903a583ea82a1c4c',
			# 'X-User-Experience-ID': str(uuid.uuid1()),
		})
		if self.RCR.request_to_post(page_type='json'):  # page_type='json'
			if 'httpStatusCode' in str(self.RCR.page_source):
				self.logger.info("获取质检信息有误 (*>﹏<*)【detail】")
				self.callback_msg = "获取质检信息有误"
				return False
			elif "data" in str(self.RCR.page_source):
				return True
			else:
				return False
		self.logger.info("详情超时或者错误(*>﹏<*)【detail】")
		self.callback_msg = "详情超时或者错误"
		return False
	
	def process_to_segment(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		# # # 从详情页收集航段信息
		self.order_status, temp_list = self.BPR.parse_to_path('$..confirmationNumber', self.RCR.page_source)
		# self.logger.info(self.order_status)
		if self.order_status:
			self.order_status = "Confirmation"
		tripType = 0
		bounds, bounds_list = self.BPR.parse_to_path('$...bounds', self.RCR.page_source)
		# 遍历航司，
		for i in bounds:
			dep_time, temp_list = self.BPR.parse_to_path('$.departureTime', i)
			air_time, temp_list = self.BPR.parse_to_path('$.arrivalTime', i)
			dep_time = self.DFR.format_to_transform(dep_time, "%H:%M").strftime('%H%M')
			air_time = self.DFR.format_to_transform(air_time, "%H:%M").strftime('%H%M')
			# 出发日期, 到达日期
			departureDateTime, departureDateTime_list = self.BPR.parse_to_path('$..departureDateTime', i)
			arrivalDateTime, arrivalDateTime_list = self.BPR.parse_to_path('$..arrivalDateTime', i)
			# 航班号
			flight_num, temp_list = self.BPR.parse_to_path('$..flightNumber', i)
			# 航班号二字码  WN
			operatingCarrierCode, temp_list = self.BPR.parse_to_path('$..operatingCarrierCode', i)
			# 出发到达机场三字码
			originationAirportCode, temp_list = self.BPR.parse_to_path('$.originationAirportCode', i)
			destinationAirportCode, temp_list = self.BPR.parse_to_path('$.destinationAirportCode', i)
			tripType += 1
			self.segments.append({
				"departureAircode": originationAirportCode, "arrivalAircode": destinationAirportCode,
				"flightNum": operatingCarrierCode + flight_num,
				"departureTime": departureDateTime.replace('-', '').split('T')[0] + dep_time,
				"arrivalTime": arrivalDateTime.replace('-', '').split('T')[0] + air_time,
				"tripType": tripType
			})
		return True
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		passengers, passengers_list = self.BPR.parse_to_path('$...passengers', self.RCR.page_source)
		for i in passengers:
			# 名字
			first_name, temp_list = self.BPR.parse_to_path('$..firstName', i)
			middle_name, temp_list = self.BPR.parse_to_path('$..middleNames', i)
			if middle_name:
				first_name = first_name + " " + middle_name
			last_name, temp_list = self.BPR.parse_to_path('$..lastName', i)
			# 生日
			birthDate, temp_list = self.BPR.parse_to_path('$..birthDate', i)
			# 性别
			gender, temp_list = self.BPR.parse_to_path('$..gender', i)
			self.passengers.append({
				"passengerName": f"{last_name}/{first_name}",  # f"{last_name}/{first_name}"
				"passengerBirthday": birthDate,
				"passengerSex": gender,
				"passengerType": 0,
				"passengerNationality": "",
				"identificationNumber": "",
				"cardType": "", "cardExpired": "",
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