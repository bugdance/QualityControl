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


class PersTTScraper(RequestWorker):
	"""TT采集器

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
		# # # 请求中用到的变量
		self.verify_token: str = ""  # 认证token
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
		
		if self.process_to_index():
			if self.process_to_login():
				if self.process_to_search():
					if self.process_to_detail():
						if self.process_to_segment():
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
		# # # 爬取首页
		self.RCR.url = "https://tigerair.com.au/"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Upgrade-Insecure-Requests': '1',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-User': '?1',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'none',
			
		})
		if self.RCR.request_to_get():
			return True
		return False
	
	def process_to_login(self) -> bool:
		"""查询登录信息流程
        :return:  bool
        """
		# # # 爬取登录页面
		self.RCR.url = "https://manage.tigerair.com.au/tigerairmmb/manage/retrievebooking"
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Sec-Fetch-Site': 'same-site',
			'Referer': 'https://tigerair.com.au/',
		})
		if self.RCR.request_to_get():
			return True
		return False
	
	def process_to_search(self) -> bool:
		"""查询详情信息流程
        :return:  bool
        """
		# # # 从登录页爬取详情页
		self.RCR.url = "https://manage.tigerair.com.au/TigerAirMMB/Manage/RetrieveBooking"
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Origin': 'https://manage.tigerair.com.au',
			'Content-Type': 'application/x-www-form-urlencoded',
			'Sec-Fetch-Site': 'same-origin',
			'Referer': 'https://manage.tigerair.com.au/tigerairmmb/manage/retrievebooking',
		})
		self.CPR.first_name = self.BPR.parse_to_replace(' +', ' ', self.CPR.first_name)
		self.RCR.post_data = {
			"Reloc": self.CPR.record,
			"LastName": self.CPR.last_name,
			"FirstName": self.CPR.first_name
		}
		if self.RCR.request_to_post(is_redirect=True):
			if 'We cannot locate your booking at this time' in self.RCR.page_source:
				self.RCR.post_data = [
					("Reloc", self.CPR.record),
					("LastName", self.CPR.last_name),
					("FirstName", self.CPR.first_name.replace(" ", ''))
				]
				if self.RCR.request_to_post(is_redirect=True):
					if 'Booking cannot be retrieved as one or more passengers are checked in for this flight' in self.RCR.page_source:
						self.callback_msg = "已经值机，请人工处理"
						return False
					if 'We cannot locate your booking at this time' in self.RCR.page_source:
						self.logger.info("接口传入数据错误(*>﹏<*)")
						self.callback_msg = "接口数据错误"
						return False
					elif "blocked" in self.RCR.page_source:
						self.logger.info("代理失效(*>﹏<*)")
						self.callback_msg = "代理失效"
						return False
					else:
						return True
				else:
					self.callback_msg = "请求乘客信息页面出错"
					return False
			elif "blocked" in self.RCR.page_source:
				self.logger.info("代理失效(*>﹏<*)")
				self.callback_msg = "代理失效"
				return False
			else:
				self.callback_msg = "请求乘客信息页面出错"
				return True
		else:
			return False
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		# # # 从详情页收集乘客信息
		
		passenger, temp_list = self.DPR.parse_to_attributes(
			"text", "css", 'span[class="passenger-name"]', self.RCR.page_source)
		if temp_list:
			for psg in temp_list:
				if psg[-1] == ' ':
					psgName = psg.split(' ')[1:-1]
				else:
					psgName = psg.split(' ')
				lastName = psgName[-1]
				firstName = ' '.join(psgName[0:-1])
				passengerName = lastName + '/' + firstName
				gender = psg.split(' ')[0]
				Female = ["MS", "MRS", "MISS"]
				adult = ["MR", "MS", "MRS"]
				if gender in Female:
					passengerSex = 'F'
				else:
					passengerSex = 'M'
				if gender in adult:
					passengerType = '0'
				else:
					passengerType = '1'
				self.passengers.append({
					"cardExpired": "",
					"cardType": "",
					"identificationNumber": "",
					"passengerBirthday": "",
					"passengerName": passengerName,
					"passengerNationality": "",
					"passengerSex": passengerSex,
					"passengerType": passengerType,
					"service_type": ""
				})
			return True
		self.logger.info("乘客超时或者错误(*>﹏<*)【passengers】")
		self.callback_msg = "乘客超时或者错误"
		
		return False
	
	def process_to_segment(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		
		# # # 从详情页收集航段信息
		self.order_status, so_list = self.DPR.parse_to_attributes("text", "css", '[id="reserveStatus"]',
		                                                          self.RCR.page_source)
		self.CPR.record, tn_list = self.DPR.parse_to_attributes("text", "css", '[id="PNRNumber"] h2',
		                                                        self.RCR.page_source)
		segments, temp_list = self.DPR.parse_to_attributes('text', 'css', '.single-flight-block', self.RCR.page_source)
		if temp_list:
			for i, v in enumerate(temp_list):
				city_code, city_list = self.DPR.parse_to_attributes('text', 'css', 'span[class="port-code"]',
				                                                    self.RCR.page_source)
				dep_code = city_list[2 * i].replace(' ', '').replace('\n', '').replace('\r', '')
				arr_code = city_list[2 * i + 1].replace(' ', '').replace('\n', '').replace('\r', '')
				date, date_list = self.DPR.parse_to_attributes('text', 'css', 'span[class="flight-date"]',
				                                               self.RCR.page_source)
				dep_date = date_list[i].replace(' ', '').replace('\n', '').replace('\r', '')
				time, time_list = self.DPR.parse_to_attributes('text', 'css', 'span[class="flight-time"]',
				                                               self.RCR.page_source)
				dep_time = time_list[2 * i].replace(' ', '').replace('\n', '').replace('\r', '')
				arr_time = time_list[2 * i + 1].replace(' ', '').replace('\n', '').replace('\r', '')
				is_return, ir_list = self.DPR.parse_to_attributes('text', 'css', '[class="flight-date-details"] h4',
				                                                  self.RCR.page_source)
				is_ret = ir_list[i]
				flight_num, fn_list = self.DPR.parse_to_attributes('text', 'css', 'span[class="flight-number"]',
				                                                   self.RCR.page_source)
				flight_number = fn_list[i].replace(' ', '').replace('\n', '').replace('\r', '')
				if is_ret == 'Departing Date':
					tripType = '1'
				else:
					tripType = '2'
				dep_date = self.DFR.format_to_transform(dep_date, "%b%d%Y").strftime('%Y%m%d')
				dep_time = self.DFR.format_to_transform(dep_time, "%I:%M%p", ).strftime('%H%M')
				arr_time = self.DFR.format_to_transform(arr_time, "%I:%M%p", ).strftime("%H%M")
				if int(arr_time) < int(dep_time):
					arr_date = self.DFR.format_to_transform(dep_date, "%Y%m%d")
					arr_date = self.DFR.format_to_custom(arr_date, custom_days=1)
					arr_date = arr_date.strftime("%Y%m%d")
				else:
					arr_date = dep_date
				dep_time = dep_date + dep_time
				arr_time = arr_date + arr_time
				self.segments.append({
					"arrivalAircode": arr_code,
					"arrivalTime": arr_time,
					"departureAircode": dep_code,
					"departureTime": dep_time,
					"flightNum": flight_number,
					"tripType": tripType
				})
			return True
		self.logger.info("航段超时或者错误(*>﹏<*)【segments】")
		self.callback_msg = "航段超时或者错误"
		return False
	
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

