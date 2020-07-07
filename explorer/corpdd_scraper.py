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
from collector.corpdd_mirror import CorpDDMirror
import random
import time


class CorpDDScraper(RequestWorker):
	"""DD采集器，全部首页质检
    """
	
	def __init__(self):
		RequestWorker.__init__(self)
		self.RCR = RequestCrawler()  # 请求爬行器。
		self.AFR = AESFormatter()  # AES格式器。
		self.BFR = BasicFormatter()  # 基础格式器。
		self.BPR = BasicParser()  # 基础解析器。
		self.CFR = CallBackFormatter()  # 回调格式器。
		self.CPR = CallInParser()  # 接入解析器。
		self.DFR = DateFormatter()  # 日期格式器。
		self.DPR = DomParser()  # 文档解析器。
		self.CMR = CorpDDMirror()  # DD镜像器
		# # # 请求中用到的变量
		self.verify_token: str = ""  # 认证token
		# # # 返回中用到的变量
		self.order_status: str = ""  # 订单状态
		self.segments: list = []  # 航段信息
		self.passengers: list = []  # 乘客信息
		
		self.temp_source: str = ""  # 临时源数据
	
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
		self.CMR.logger = self.logger
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
		self.user_agent, self.init_header = self.RCR.build_to_header("None")
		# # # 质检流程
		if self.process_to_index():
			if self.process_to_login():
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
	
	def process_to_index(self, count: int = 0, max_count: int = 2) -> bool:
		"""首页查询航班流程
        :return:  bool
        """
		if count >= max_count:
			return False
		
		# # # 爬取首页
		self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/aspx/AgentLogin.aspx?ReturnUrl=%2fNokSmileBooking%2faspx"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
			"Host": "b2b.nokair.com",
			"Sec-Fetch-Mode": "navigate",
			"Sec-Fetch-Site": "none",
			"Upgrade-Insecure-Requests": "1",
		})
		if self.RCR.request_to_get():
			self.temp_source = self.RCR.page_source
			return True
		
		self.logger.info(f"首页超时或者错误(*>﹏<*)【{self.RCR.url}】")
		self.callback_msg = "首页超时或者错误"
		return self.process_to_index(count + 1, max_count)
	
	def process_to_login(self, count: int = 0, max_count: int = 2) -> bool:
		"""

		Returns:

		"""
		if count >= max_count:
			return False
		
		view_state, temp_list = self.DPR.parse_to_attributes(
			"value", "css", '[id="__VIEWSTATE"]', self.temp_source)
		if not view_state:
			self.callback_msg = "view_state 获取失败"
			return False
		generator, temp_list = self.DPR.parse_to_attributes(
			"value", "css", '[id="__VIEWSTATEGENERATOR"]', self.temp_source)
		if not generator:
			self.callback_msg = "generator 获取失败"
			return False
		validation, temp_list = self.DPR.parse_to_attributes(
			"value", "css", '[id="__EVENTVALIDATION"]', self.temp_source)
		if not validation:
			self.callback_msg = "validation 获取失败"
			return False
		self.CPR.username = "BJNTL"
		self.CPR.password = 'Noknok2019'
		self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/aspx/AgentLogin.aspx?ReturnUrl=%2fNokSmileBooking%2faspx"
		self.RCR.post_data = {
			"__VIEWSTATE": view_state,
			"__VIEWSTATEGENERATOR": generator,
			"__EVENTVALIDATION": validation,
			"txtLastName": self.CPR.username,
			"txtBookingNo": self.CPR.password,
			"bttLogin.x": str(random.randint(35, 50)),
			"bttLogin.y": str(random.randint(5, 30)),
		}
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
			"Content-Type": "application/x-www-form-urlencoded",
			"Upgrade-Insecure-Requests": "1",
			"Host": "b2b.nokair.com",
			"Origin": "https://b2b.nokair.com",
			"Referer": "https://b2b.nokair.com/NokSmileBooking/aspx/AgentLogin.aspx?ReturnUrl=%2fNokSmileBooking%2faspx",
		})
		if self.RCR.request_to_post(status_code=302):
			self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/aspx"
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.param_data = None
			self.RCR.header.update({
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
				"Host": "b2b.nokair.com",
				"Referer": "https://b2b.nokair.com/NokSmileBooking/aspx/AgentLogin.aspx?ReturnUrl=%2fNokSmileBooking%2faspx",
				"Upgrade-Insecure-Requests": "1",
			})
			if self.RCR.request_to_get(status_code=301):
				self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/aspx/AgentLogin.aspx?ReturnUrl=%2fNokSmileBooking%2faspx"
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
					"Host": "b2b.nokair.com",
					"Upgrade-Insecure-Requests": "1",
				})
				if self.RCR.request_to_get(status_code=302):
					self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/aspx/noksmile.aspx"
					self.RCR.header = self.BFR.format_to_same(self.init_header)
					self.RCR.header.update({
						"Host": "b2b.nokair.com",
						'authority': 'b2b.nokair.com',
						'pragma': 'no-cache',
						'cache-control': 'no-cache',
						'upgrade-insecure-requests': '1',
						'sec-fetch-dest': 'document',
						'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
						'sec-fetch-site': 'same-origin',
						'sec-fetch-mode': 'navigate',
						'sec-fetch-user': '?1',
						'referer': 'https://b2b.nokair.com/NokSmileBooking/aspx/AgentLogin.aspx?ReturnUrl=%2fNokSmileBooking%2faspx%2fnoksmile.aspx',
					})
					if self.RCR.request_to_get():
						if "168033518@qq.com" in self.RCR.page_source and "account_info" in self.RCR.page_source:
							self.logger.info("登录成功")
							return True
						else:
							self.logger.info("登录失败, 未找到账户信息")
							self.callback_msg = "登录失败, 未找到账户信息"
							return False
		
		self.logger.info("账号登录失败")
		self.callback_msg = "账号登录失败"
		return self.process_to_login(count + 1, max_count)
	
	def process_to_search(self):
		"""

		Returns:

		"""
		self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/NokSmile/PageHandler.aspx"
		self.RCR.param_data = (
			("v", "BM01"),
			("BookingNo", self.CPR.record),
			("PaxName", ""),
			("CreateDate", "")
		)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"X-Requested-With": "XMLHttpRequest",
			"Referer": "https://b2b.nokair.com/NokSmileBooking/aspx/NokBooking.aspx",
			"Origin": "https://b2b.nokair.com",
			"Host": "b2b.nokair.com",
			"Accept": "*/*",
		})
		if self.RCR.request_to_post():
			self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/NokSmile/NokAuthen.aspx"
			self.RCR.param_data = (
				("BookingNo", self.CPR.record),
			)
			if self.RCR.request_to_post():
				self.RCR.url = "https://b2b.nokair.com/NokSmileBooking/aspx/ViewYourBooking.aspx"
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					"X-Requested-With": "XMLHttpRequest",
					"Referer": "https://b2b.nokair.com/NokSmileBooking/aspx/NokBooking.aspx",
					"Origin": "https://b2b.nokair.com",
					"Host": "b2b.nokair.com",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
					"Upgrade-Insecure-Requests": "1",
				})
				if self.RCR.request_to_post():
					return True
		self.logger.info(f"票号查询失败【{self.RCR.url}】")
		self.callback_msg = "详票号查询失败"
		return False
	
	def process_to_segment(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		# 判断页面是否存在 PNR
		pnr, temp_list = self.DPR.parse_to_attributes(
			"text", "css", '[id="Body_Content_BookingInfo1_lblBookingNo"]', self.RCR.page_source)
		if pnr:
			self.order_status, temp_list = self.DPR.parse_to_attributes(
				"text", "css", '[id="Body_Content_BookingInfo1_lblPayStatus"]', self.RCR.page_source)
			# if self.order_status == "COMPLETED":
			#     self.order_status = "Confirmed"
			# # # # 解析时间
			flight_time, flight_time_list = self.DPR.parse_to_attributes(
				"text", "css", 'td[width="135"][height="4"][valign="top"]', self.RCR.page_source)
			self.temp_list = [nums for nums in range(len(flight_time_list))]  # 判断是否是往返， 如果是往返返回 0， 1
			for nums in range(len(flight_time_list)):
				# 航班日期
				flight_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", flight_time_list[nums])
				concrete_time, concrete_time_list = self.DPR.parse_to_attributes('text', 'xpath',
				                                                                 '//td[@width="190"][@valign="top"][@height="37"]/span/text()[2]',
				                                                                 self.RCR.page_source)
				flight_number, flight_number_list = self.DPR.parse_to_attributes('text', 'css',
				                                                                 'td[width="75"][height="37"][valign="top"] span[class="bodyBC"]',
				                                                                 self.RCR.page_source)
				flight_code, flight_code_list = self.DPR.parse_to_attributes(
					"text", "css",
					'td[width="190"][height="37"][valign="top"] span', self.RCR.page_source)
				from_date = ''  # 出发时间
				to_date = ''  # 到达时间
				dep_code = ''  # 出发地
				arr_code = ''  # 目的地
				if nums == 0:
					from_date = self.DFR.format_to_transform(flight_time + str(concrete_time_list[0]),
					                                         '%a,%d%b%Y%H:%M')
					to_date = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", concrete_time_list[1])
					to_date = self.DFR.format_to_transform(flight_time + to_date, '%a,%d%b%Y%H:%M')
					flight_number = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", flight_number_list[nums])
					for i in self.CMR._country_code.items():
						if i[1] == flight_code_list[0]:
							dep_code = i[0]
						elif i[1] == flight_code_list[1]:
							arr_code = i[0]
				elif nums == 1:
					from_date = self.DFR.format_to_transform(flight_time + str(concrete_time_list[2]),
					                                         '%a,%d%b%Y%H:%M')
					to_date = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", concrete_time_list[3])
					to_date = self.DFR.format_to_transform(flight_time + to_date, '%a,%d%b%Y%H:%M')
					flight_number = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", flight_number_list[2])
					for i in self.CMR._country_code.items():
						if i[1] == flight_code_list[2]:
							dep_code = i[0]
						elif i[1] == flight_code_list[3]:
							arr_code = i[0]
					# 航班号
				else:
					self.callback_msg = "【 航段信息解析失败 】"
					return False
				from_date = from_date.strftime("%Y%m%d%H%M")
				to_date = to_date.strftime("%Y%m%d%H%M")
				if int(to_date) < int(from_date):
					to_date = self.DFR.format_to_transform(to_date, "%Y%m%d%H%M")
					to_date = self.DFR.format_to_custom(to_date, custom_days=1)
					to_date = to_date.strftime("%Y%m%d%H%M")
				self.segments.append({
					"departureAircode": dep_code,
					"arrivalAircode": arr_code,
					"flightNum": flight_number,
					"departureTime": from_date,
					"arrivalTime": to_date,
					"tripType": nums + 1
				})
			return True
		else:
			self.callback_msg = f"查不到订单【{self.CPR.record}】"
			return False
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		# # # 从详情页收集乘客信息
		# 乘客性别
		gender, gender_list = self.DPR.parse_to_attributes('text', 'css',
		                                                   '[id*="Body_Content_BookingPassengerInfo1_rptPaxsInfo_lblTitle_"]',
		                                                   self.RCR.page_source)
		# 乘客姓名
		name, name_list = self.DPR.parse_to_attributes('text', 'css',
		                                               '[id*="Body_Content_BookingPassengerInfo1_rptPaxsInfo_lblPaxName_"]',
		                                               self.RCR.page_source)
		# 乘客类型
		passenger_type, passenger_type_list = self.DPR.parse_to_attributes('text', 'css',
		                                                                   '[id*="Body_Content_BookingPassengerInfo1_rptPaxsInfo_lblPaxType_"]',
		                                                                   self.RCR.page_source)
		# # 乘客增值服务
		# serve, serve_include_list = self.DPR.parse_to_attributes('text', 'css',
		#                                                          'td[width="75"][height="20"][valign="middle"]:nth-child(4)',
		#                                                          self.RCR.page_source)
		# serves_Nok, serve_Nok_list = self.DPR.parse_to_attributes('text', 'css',
		#                                                           'td[width="75"][height="20"][valign="middle"]:nth-child(6)',
		#                                                           self.RCR.page_source)
		n = 0
		for i in range(len(gender_list)):
			name = name_list[i].split(' ')
			last_name = name.pop(-1)
			first_name = ' '.join(name)
			# 判断性别,
			# M 男性
			if gender_list[i] == "MR" or gender_list[i] == "BOY":
				gender = 'M'
			# F 女性
			elif gender_list[i] == "MS" or gender_list[i] == "GIRL":
				gender = 'F'
			else:
				self.logger.info(f"未知性别 (*>﹏<*) 【{gender_list[i]}】")
				self.callback_msg = "性别解析有误"
				return False
			# 判断是乘客是否是成人或儿童
			if passenger_type_list[i] == "ADULT":
				passenger_type = 0
			elif passenger_type_list[i] == "CHILD":
				passenger_type = 1
			else:
				self.logger.info("乘客类型解析失败 (*>﹏<*) ")
				self.callback_msg = f"乘客类型解析失败{passenger_type_list[i]}"
				return False
			
			# 解析行李
			appreciation = []
			# 如果是第一个人则 tr = 6/7  第二个人则是 10/11
			# p:nth-last-child(2)  从最后一个子元素开始计数
			# p:nth-child(2)       选择属于其父元素的第二个子元素的每个 <p> 元素。
			# 遍历乘客行李
			
			serve_include_list = []  # 航班自带行李
			serve = ""  # 航班自带行李
			serve_Nok_list = []  # 额外购买的行李
			serves_Nok = ""  # 额外购买的行李
			appreciation = []  # 返回行李信息
			passenge, passenge_list = self.DPR.parse_to_attributes("text", "css",
			                                                       f'table[class="Text_body"] tr:nth-of-type({6 + n}) td[valign="top"] span[class="Text_passenger"]',
			                                                       self.RCR.page_source)
			
			if last_name in str(passenge_list):
				for flight_type in self.temp_list:  # 判断航班是否是往返
					if flight_type == 0:
						# 提取行李信息
						serve, serve_include_list = self.DPR.parse_to_attributes('text', 'css',
						                                                         f'table[class="Text_body"] tr:nth-of-type({6 + n}) td[width="75"][height="20"][valign="middle"]:nth-child(4)',
						                                                         self.RCR.page_source)
						
						serves_Nok, serve_Nok_list = self.DPR.parse_to_attributes('text', 'css',
						                                                          f'table[class="Text_body"] tr:nth-of-type({6 + n}) td[width="75"][height="20"][valign="middle"]:nth-child(6)',
						                                                          self.RCR.page_source)
					
					elif flight_type == 1:
						# 提取行李信息
						serve, serve_include_list = self.DPR.parse_to_attributes('text', 'css',
						                                                         f'table[class="Text_body"] tr:nth-of-type({7 + n}) td[height="22"][valign="middle"]:nth-child(3)',
						                                                         self.RCR.page_source)
						
						serves_Nok, serve_Nok_list = self.DPR.parse_to_attributes('text', 'css',
						                                                          f'table[class="Text_body"] tr:nth-of-type({7 + n}) td[height="22"][valign="middle"]:nth-child(5)',
						                                                          self.RCR.page_source)
					
					serve = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|kg", "", serve)
					serves_Nok = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|kg", "", serves_Nok)
					
					if serve != "":
						serve = int(serve)
					else:
						serve = 0
					if serves_Nok != "":
						serves_Nok = int(serves_Nok)
					else:
						serves_Nok = 0
					luggage_combined = serve + serves_Nok
					if luggage_combined != 0:
						appreciation.append({
							"productType": "1",
							"detail": str(luggage_combined) + "KG",
							"departureAircode": self.segments[flight_type].get('departureAircode'),
							"arrivalAircode": self.segments[flight_type].get('arrivalAircode'),
							"tripType": flight_type + 1
						})
			
			# if self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve)
			
			# # 判断机票自带的行李是否为 0KG
			# if self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve_include_list[i]).upper() == "0KG":
			# 	appreciation = []
			# 	# 判断是否添加了行李
			# 	if "KG" not in self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve_Nok_list[i]).upper():
			# 		appreciation = []
			# 	else:
			# 		for serve_Nok in serve_Nok_list:
			# 			if "kg" in serve_Nok:
			# 				appreciation.append({
			# 					"detail": self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve_Nok).upper(),
			# 					"productType": "1",
			# 					"departureAircode": "",
			# 					"arrivalAircode": "",
			# 					"tripType": flight_type + 1
			# 				})
			# else:
			# 	include_luggage = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|kg", "", serve_include_list[i])
			# 	for flight_type in self.temp_list:
			# 		# 如果机票自带了行李，未添加额外行李
			# 		if "KG" not in self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "",
			# 												 serve_Nok_list[i]).upper():
			# 			appreciation.append({
			# 				"detail": str(include_luggage) + "KG",
			# 				"productType": "1",
			# 				"departureAircode": "",
			# 				"arrivalAircode": "",
			# 				"tripType": flight_type + 1
			# 			})
			# 		else:
			# 			# 当添加行李也不为空， 则行李 公斤数 相加
			# 			nok_luggage = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|kg", "", serve_Nok_list[i])
			# 			appreciation.append({
			# 				"detail": str(int(include_luggage) + int(nok_luggage)) + "KG",
			# 				"productType": "1",
			# 				"departureAircode": "",
			# 				"arrivalAircode": "",
			# 				"tripType": flight_type + 1
			# 			})
			#
			
			n += 4
			
			# 	# 提取行李信息
			# 	serve, serve_include_list = self.DPR.parse_to_attributes('text', 'css',
			# 															 f'table[class="Text_body"] tr:nth-of-type() td[width="75"][height="20"][valign="middle"]:nth-child(4)',
			# 															 self.RCR.page_source)
			#
			# 	serves_Nok, serve_Nok_list = self.DPR.parse_to_attributes('text', 'css',
			# 															  'table[class="Text_body"] tr:nth-of-type(7) td[width="75"][height="20"][valign="middle"]:nth-child(6)',
			# 															  self.RCR.page_source)
			# if flight_type == 0 and i == 0:
			# 	serve, serve_include_list = self.DPR.parse_to_attributes('text', 'css',
			# 															 'table[class="Text_body"] tbody tr[]:nth-child(6) td[width="75"][height="20"][valign="middle"]:nth-child(4)',
			# 															 self.RCR.page_source)
			# 	self.logger.info(serve_include_list)
			#
			# 	serves_Nok, serve_Nok_list = self.DPR.parse_to_attributes('text', 'css',
			# 															  'table[class="Text_body"] tbody tr[]:nth-child(6) td[width="75"][height="20"][valign="middle"]:nth-child(6)',
			# 															  self.RCR.page_source)
			self.passengers.append({
				"passengerName": f"{last_name}/{first_name}",  # f"{last_name}/{first_name}"
				"passengerBirthday": "",
				"passengerSex": gender,
				"passengerType": passenger_type,
				"passengerNationality": "",
				"identificationNumber": "",
				"cardType": "", "cardExpired": "",
				"service_type": "",
				"auxArray": appreciation
			})
		# self.logger.info(self.passengers)
		# time.sleep(10000)
		
		#
		#
		# 		# 判断乘客
		# 		if i == 0:
		# 			# 乘客增值服务
		# 			serve, serve_include_list = self.DPR.parse_to_attributes('text', 'css',
		# 																	 'td[width="75"][height="20"][valign="middle"]:nth-child(4)',
		# 																	 self.RCR.page_source)
		#
		# 			serves_Nok, serve_Nok_list = self.DPR.parse_to_attributes('text', 'css',
		# 																	  'td[width="75"][height="20"][valign="middle"]:nth-child(6)',
		# 																	  self.RCR.page_source)
		#
		# 	# 判断机票自带的行李是否为 0KG
		# 	if self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve_include_list[i]).upper() == "0KG":
		# 		appreciation = []
		# 		# 判断是否添加了行李
		# 		if "KG" not in self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve_Nok_list[i]).upper():
		# 			appreciation = []
		# 		else:
		# 			for flight_type in self.temp_list:
		# 				if "kg" in serve_Nok_list[i]:
		# 					self.logger.info(serve_Nok_list)
		# 					appreciation.append({
		# 						"detail": self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve_Nok_list[i]).upper(),
		# 						"productType": "1",
		# 						"departureAircode": "",
		# 						"arrivalAircode": "",
		# 						"tripType": flight_type + 1
		# 					})
		# 	else:
		# 		include_luggage = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|kg", "", serve_include_list[i])
		# 		for flight_type in self.temp_list:
		# 			# 如果机票自带了行李，未添加额外行李
		# 			if "KG" not in self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", serve_Nok_list[i]).upper():
		# 				appreciation.append({
		# 					"detail": str(include_luggage) + "KG",
		# 					"productType": "1",
		# 					"departureAircode": "",
		# 					"arrivalAircode": "",
		# 					"tripType": flight_type + 1
		# 				})
		# 			else:
		# 				# 当添加行李也不为空， 则行李 公斤数 相加
		# 				nok_luggage = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|kg", "", serve_Nok_list[i])
		# 				appreciation.append({
		# 					"detail": str(int(include_luggage) + int(nok_luggage)) + "KG",
		# 					"productType": "1",
		# 					"departureAircode": "",
		# 					"arrivalAircode": "",
		# 					"tripType": flight_type + 1
		# 				})
		
		return True
	
	# self.logger.info("乘客超时或者错误(*>﹏<*)【passengers】")
	# self.callback_msg = "乘客超时或者错误"
	# return False
	
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
