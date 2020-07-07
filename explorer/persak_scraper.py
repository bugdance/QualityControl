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
from detector.persak_simulator import PersAKSimulator
import random
import time


class PersAKScraper(RequestWorker):
	"""AK采集器，首页质检
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
		self.PSR = PersAKSimulator()
		# # # 返回中用到的变量
		self.order_status: str = ""  # 订单状态
		self.segments: list = []  # 航段信息
		self.passengers: list = []  # 乘客信息
		# 请求中用到的变量
		self.api_key: str = ""
		self.client_id: str = ""
		self.access_token: str = ""
		self.user_id: str = ""
		self.loyalty_id: str = ""

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
		self.PSR.logger = self.logger
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
		self.user_agent, self.init_header = self.RCR.build_to_header("Firefox")
		# # # 质检流程
		# if self.requests_home():
		# # # 不走登录查询， 有点小问题，需要修改
		# if self.process_to_index():
		#     if self.query_from_detail():
		#         if self.query_from_passenger():
		#             if self.login_collect_to_segments():
		#                 if self.query_from_loggin_gender():
		#                     if self.process_to_detail():
		# 	                    self.process_to_return()
		# 	                    self.logger.removeHandler(self.handler)
		# 	                    return self.callback_data
		if self.get_proxy():

			if self.process_to_verify():
				if self.process_to_login():
					if self.query_from_login():
						if self.query_from_loggin_passenger():
							if self.login_collect_to_segments():
								if self.query_from_loggin_gender():
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

	def get_proxy(self, count: int = 0, max_count: int = 4):
		"""
        判断代理，在规定时间段内使用
        :return:
        """
		if count >= max_count:
			return False
		else:
			self.RCR.timeout = 5
			# 判断当前时间是否在 00:00 - 05:30 时间段， 如果符合则使用代理，否则不使用
			current_time = self.DFR.format_to_now()
			now = time.strptime(current_time.strftime('%H%M'), "%H%M")  # 当前时间
			if time.strptime('0000', "%H%M") < now < time.strptime('2330', "%H%M"):

				self.RCR.set_to_proxy(False, "")
				# 获取代理， 并配置代理
				# 托马斯
				# log_account = account[random.randint(0, len(account) - 1)]
				service_type = ["3", "4", "112"]
				self.RCR.url = 'http://cloudmonitorproxy.51kongtie.com/Proxy/getProxyByServiceType?proxyNum=1&serviceType=' + \
							   service_type[random.randint(0, 2)]
				# 塔台
				# self.RCR.url = 'http://cloudmonitorproxy.51kongtie.com/Proxy/getProxyByServiceType?proxyNum=1&serviceType=112'
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.param_data = None
				if self.RCR.request_to_get('json'):
					for ip in self.RCR.page_source:
						if ip.get('proxyIP'):
							self.proxys = "http://yunku:123@" + str(ip.get('proxyIP')) + ":" + str(ip.get('prot'))
							# self.proxys = "http://yunku:123@" + "60.179.17.209" + ":" + "3138"
							self.RCR.set_to_proxy(enable_proxy=True, address=self.proxys)
							return True
						else:
							self.callback_msg = f"代理地址获取失败"
							self.logger.info(self.callback_msg)
							return self.get_proxy(count + 1, max_count)
				else:
					# self.RCR.set_to_proxy(enable_proxy=True, address='http://yunku:123@120.5.51.17:3138')
					self.callback_msg = f"代理地址获取失败"
					self.logger.info(self.callback_msg)
					return self.get_proxy(count + 1, max_count)
			# return True
			else:
				# self.RCR.set_to_proxy(enable_proxy=True, address='http://yunku:123@120.5.51.17:3138')
				self.callback_msg = f"代理超出使用时间段【当前时间：{current_time}】"
				# 1, False 超出使用时间不跑。
				# 2, True  超出使用时间继续跑, 不使用代理。
				return False
	
	def requests_home(self):
		"""
		
		Returns:

		"""
		# 请求首页
		self.RCR.url = "https://www.airasia.com/en/gb"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
			"Host": "www.airasia.com",
			"Sec-Fetch-Mode": "same-origin",
			"Sec-Fetch-Site": "same-origin",
			"Upgrade-Insecure-Requests": "1",
		})
		if self.RCR.request_to_get():
			return True
		else:
			self.callback_msg = f"【{self.RCR.url}】请求首页失败"
			return False
	
	def process_to_verify(self, count: int = 0, max_count: int = 3) -> bool:
		"""

		Returns:

		"""
		# # # 解析登录需要参数
		if count >= max_count:
			return False
		self.RCR.timeout = 10
		self.RCR.set_to_cookies(False, [{
			"name": "userSession", "value": "cc=zh-cn&mcc=MYR&rc=WWWA&ad=&p=&st=1513153810.36725&rsc=0",
			# "domain": ".airasia.com", "path": "/"
		}])
		self.RCR.url = "https://www.airasia.com/en/gb"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Host": "www.airasia.com",
			"Upgrade-Insecure-Requests": "1"
		})
		if self.RCR.request_to_get():
			# 提交真正，并获取 Token
			if self.getssrdata():
				return True
			
			self.callback_msg = "认证失败"
			self.get_proxy()
			return self.process_to_verify(count + 1, max_count)
		
		self.callback_msg = "请求首页失败"
		self.get_proxy()
		return self.process_to_verify(count + 1, max_count)
	
	def process_to_login(self, count: int = 0, max_count: int = 4):
		"""
        登录账号
        count 重试次数
        max_count 最大重试次数
        :return:
        """
		self.RCR.timeout = 15
		# 随机返回账号，
		account = ['168033518@qq.com', '2765590455@qq.com', '1077473443@qq.com']
		self.CPR.username = account[random.randint(0, 2)]
		self.CPR.password = 'Su123456'
		
		if count >= max_count:
			return False
		else:
			# # # 进行登录
			self.RCR.url = "https://ssor.airasia.com/config/v2/clients/by-origin"
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "application/json, text/plain, */*",
				"Host": "ssor.airasia.com",
				"Origin": "https://www.airasia.com",
				"Referer": "https://www.airasia.com/en/gb"
			})
			if self.RCR.request_to_get("json"):
				self.client_id, temp_list = self.BPR.parse_to_path("$.id", self.RCR.page_source)
				self.api_key, temp_list = self.BPR.parse_to_path("$.apiKey", self.RCR.page_source)
				
				if self.credentials():
					if self.users_data():
						return True
			
			self.callback_msg = "登录失败"
			self.get_proxy()
			return self.process_to_login(count + 1, max_count)
	
	def query_from_login(self, count: int = 0, max_count: int = 5):
		"""
        登录后， 进行查询，
        :return:
        """
		if count >= max_count:
			return False
		else:
			self.RCR.timeout = 15
			self.RCR.url = "https://booking2.airasia.com/BookingListLogin.aspx"
			self.RCR.param_data = (("culture", "en-GB"),)
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
				"Host": "booking2.airasia.com",
				"Referer": "https://www.airasia.com/en/gb",
				"Upgrade-Insecure-Requests": "1"
			})
			if self.RCR.request_to_get():

				if "__VIEWSTATEGENERATOR" not in self.RCR.page_source:
					self.callback_msg = f"预定订单列表获取失败 {self.RCR.url}"
					self.get_proxy()
					return self.query_from_login(count + 1, max_count)

				self.RCR.url = "https://ssor.airasia.com/config/v2/clients/by-origin"
				self.RCR.param_data = None
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					"Accept": "application/json",
					"Content-Type": "application/json",
					"Host": "ssor.airasia.com",
					"Origin": "https://booking2.airasia.com",
					"Referer": "https://booking2.airasia.com/BookingListLogin.aspx?culture=en-GB"
				})
				if self.RCR.request_to_get("json"):
					self.client_id, temp_list = self.BPR.parse_to_path("$.id", self.RCR.page_source)
					self.api_key, temp_list = self.BPR.parse_to_path("$.apiKey", self.RCR.page_source)
					self.RCR.url = "https://ssor.airasia.com/sso/v2/authorization"
					self.RCR.param_data = (("clientId", self.client_id),)
					self.RCR.header = self.BFR.format_to_same(self.init_header)
					self.RCR.header.update({
						"Accept": "application/json",
						"Content-Type": "application/json",
						"Host": "ssor.airasia.com",
						"Origin": "https://booking2.airasia.com",
						"Referer": "https://booking2.airasia.com/BookingListLogin.aspx?culture=en-GB",
						"X-Api-Key": self.api_key,
					})
					if self.RCR.request_to_get("json"):
						self.access_token, temp_list = self.BPR.parse_to_path("$.accessToken", self.RCR.page_source)
						refresh_token, temp_list = self.BPR.parse_to_path("$.refreshToken", self.RCR.page_source)
						user_id, temp_list = self.BPR.parse_to_path("$.userId", self.RCR.page_source)
						aa = str(self.RCR.page_source).replace(' ', '').replace('\'', '\"')
						
						self.RCR.url = f"https://ssor.airasia.com/um/v2/users/{user_id}"
						self.RCR.param_data = None
						self.RCR.header = self.BFR.format_to_same(self.init_header)
						self.RCR.header.update({
							"Accept": "application/json",
							"Content-Type": "application/json",
							"Host": "ssor.airasia.com",
							"Origin": "https://booking2.airasia.com",
							"Referer": "https://booking2.airasia.com/BookingListLogin.aspx?culture=en-GB",
							"Authorization": self.access_token,
							"X-Api-Key": self.api_key,
							"X-AA-Client-Id": self.client_id
						})
						# 获取票号数据，重试 3 次
						if self.RCR.request_to_get():
							
							bb = self.RCR.page_source
							self.RCR.url = "https://booking2.airasia.com/BookingListLogin.aspx"
							self.RCR.param_data = (("culture", "en-GB"),)
							self.RCR.header = self.BFR.format_to_same(self.init_header)
							self.RCR.header.update({
								"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
								"Content-Type": "application/x-www-form-urlencoded",
								"Host": "booking2.airasia.com",
								"Origin": "https://booking2.airasia.com",
								"Referer": "https://booking2.airasia.com/BookingListLogin.aspx?culture=en-GB",
								"Upgrade-Insecure-Requests": "1"
							})
							self.RCR.post_data = f'''data={str(aa)}&userdata={str(bb)}'''
							if self.RCR.request_to_post(is_redirect=True):
								self.RCR.url = "https://booking2.airasia.com/bookinglist.aspx"
								self.RCR.header.update({
									"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
									"Content-Type": "application/x-www-form-urlencoded",
									"Origin": "https://booking2.airasia.com",
									"Sec-Fetch-Mode": "navigate",
									"Sec-Fetch-Site": "same-origin",
									"Sec-Fetch-User": "?1",
									"Host": "booking2.airasia.com",
									"Referer": "https://booking2.airasia.com/bookinglist.aspx",
									"Upgrade-Insecure-Requests": "1"
								})
								patch_data = [
									("__EVENTTARGET", False, "ControlGroupBookingListView$BookingListSearchInputView"),
									("__EVENTARGUMENT", False, f"Edit:{self.CPR.record}"),
									("__VIEWSTATE", True, "#viewState"),
									("pageToken", False, ""),
									("MemberLoginBookingListView$HFTimeZone", False, "480"),
									("ControlGroupBookingListView$BookingListSearchInputView$TextBoxBookingNo",
									 False, "Key in your booking number"),
									("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR")
								]
								self.RCR.post_data = self.DPR.parse_to_batch("value", "css", patch_data,
								                                             self.RCR.page_source)
								if self.RCR.request_to_post():
									return True
						
						else:
							self.callback_msg = f"获取用户信息失败 {self.RCR.url}"
							self.get_proxy()
							return self.query_from_login(count + 1, max_count)
			
			else:
				self.callback_msg = f"预定列表页面获取失败 {self.RCR.url}"
				self.get_proxy()
				return self.query_from_login(count + 1, max_count)
			
			self.callback_msg = f"登录失败或获取票号数据失败 {self.RCR.url}"
			self.get_proxy()
			return self.query_from_login(count + 1, max_count)
	
	def process_to_index(self) -> bool:
		"""首页查询pnr流程
        :return:  bool
        """
		# # # 爬取首页
		self.RCR.url = 'https://booking2.airasia.com/retrieveextbooking.aspx?culture=en-gb'
		self.RCR.param_data = (("culture", "en-GB"),)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Host": "booking2.airasia.com",
			"Upgrade-Insecure-Requests": "1"
		})
		if self.RCR.request_to_get():
			return True
		self.callback_msg = "质检失败"
		return False
	
	def query_from_detail(self) -> bool:
		"""查询详情信息流程
        :return:  bool
        """
		self.RCR.url = "https://booking2.airasia.com/retrieveextbooking.aspx"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Content-Type": "application/x-www-form-urlencoded",
			"Host": "booking2.airasia.com",
			"Origin": "https://booking2.airasia.com",
			"Referer": "https://booking2.airasia.com/retrieveextbooking.aspx?culture=en-gb"
		})
		patch_data = [
			("__EVENTTARGET", True, "#eventTarget"),
			("__EVENTARGUMENT", True, "#eventArgument"),
			("__VIEWSTATE", True, "#viewState"),
			("pageToken", True, "[name=pageToken]"),
			("eventTarget", True, "#eventTarget"),
			("eventArgument", True, "#eventArgument"),
			("viewState", True, "#viewState"),
			("pageToken", True, "[name=pageToken]"),
			("MemberLoginBookingListView$HFTimeZone", False, "480"),
			("ControlGroupRetrieveBookingExpediaAKView$BookingRetrieveInputExpediaAKView$CONFIRMATIONNUMBER1",
			 False, self.CPR.record),
			("ControlGroupRetrieveBookingExpediaAKView$BookingRetrieveInputExpediaAKView$PAXLASTNAME1",
			 False, self.CPR.last_name),
			("ControlGroupRetrieveBookingExpediaAKView$BookingRetrieveInputExpediaAKView$ORIGINCITY1",
			 False, self.CPR.departure_code),
			("ControlGroupRetrieveBookingExpediaAKView$BookingRetrieveInputExpediaAKView$ButtonRetrieve",
			 False, "Search"),
			("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
		]
		self.RCR.post_data = self.DPR.parse_to_batch("value", "css", patch_data, self.RCR.page_source)
		if self.RCR.request_to_post():
			return True
		self.callback_msg = "质检失败"
		return False
	
	def query_from_passenger(self) -> bool:
		"""查询乘客信息流程
        :return:  bool
        """
		self.RCR.url = "https://booking2.airasia.com/Itinerary.aspx"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
			"Content-Type": "application/x-www-form-urlencoded",
			"Host": "booking2.airasia.com",
			"Origin": "https://booking2.airasia.com",
			"Referer": "https://booking2.airasia.com/retrieveextbooking.aspx?culture=en-gb",
		})
		if self.RCR.request_to_get():
			error_message, temp_list = self.DPR.parse_to_attributes("id", "css", "#errorSectionContent",
			                                                        self.RCR.page_source)
			if error_message:
				self.logger.info("查无此单")
				self.callback_msg = "查无此单"
				return False
			else:
				return True
		self.logger.info("查无此单")
		self.callback_msg = "质检失败"
		return False
	
	def query_from_loggin_passenger(self, count: int = 0, max_count: int = 3) -> bool:
		"""
        登录后，获取票号信息页面
        :return:
        """
		if count >= max_count:
			return False
		
		self.RCR.url = "https://booking2.airasia.com/ChangeItinerary.aspx"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update(
			{
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
				'Host': 'booking2.airasia.com',
				'Sec-Fetch-Mode': 'navigate',
				'Sec-Fetch-Site': 'none',
				'Referer': 'https://booking2.airasia.com/bookinglist.aspx',
				'Upgrade-Insecure-Requests': '1'
			})
		if self.RCR.request_to_get(is_redirect=True):
			if str(self.CPR.record) in str(self.RCR.page_source):
				self.temp_source = self.RCR.page_source
				return True

		self.callback_msg = f"返回票号信息页面失败【{self.RCR.url}】"
		return self.query_from_loggin_passenger(count + 1, max_count)
	
	def query_from_loggin_gender(self) -> bool:
		"""
        登录查询完成后，获取乘客性别信息
        :return:
        """
		# 判断订单是否支付完成
		if "Make payment" in self.RCR.page_source:
			self.callback_msg = "有未支付款项"
			return False
		self.RCR.url = "https://booking2.airasia.com/ChangeItinerary.aspx"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
			"Host": "booking2.airasia.com",
			"Referer": "https://booking2.airasia.com/bookinglist.aspx",
			"Upgrade-Insecure-Requests": "1",
			"Sec-Fetch-Site": "same-origin",
			"Sec-Fetch-User": "?1",
		})
		patch_data = [
			("__EVENTTARGET", False, "ChangeControl$LinkButtonChangeTraveler"),
			("__EVENTARGUMENT", False, ""),
			("__VIEWSTATE", True, "#viewState"),
			("pageToken", False, ""),
			("MemberLoginChangeItineraryExtView$HFTimeZone", False, "480"),
			("MemberLoginChangeItineraryView2$TextBoxUserID", False, ""),
			("hdRememberMeEmail", False, ""),
			("MemberLoginChangeItineraryView2$PasswordFieldPassword", False, ""),
			("memberLogin_chk_RememberMe", False, "on"),
			("HiddenFieldPageBookingData", False, self.CPR.record),
			("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
		]
		self.RCR.post_data = self.DPR.parse_to_batch("value", "css", patch_data, self.RCR.page_source)
		if self.RCR.request_to_post(is_redirect=True):
			return True
		else:
			self.callback_msg = "质检失败"
			return False
	
	def login_collect_to_segments(self) -> bool:
		"""
        查询完成后，提取航段信息,
        :return:
        """
		# 订单状态
		if "confirm status" in str(self.RCR.page_source):
			self.order_status, order_status_list = self.DPR.parse_to_attributes('text', 'css',
			                                                                    '[class="confirm status"]',
			                                                                    self.RCR.page_source)
		if not self.order_status:
			if "closed status" in str(self.RCR.page_source):
				self.order_status, order_status_list = self.DPR.parse_to_attributes('text', 'css',
				                                                                    '[class="closed status"]',
				                                                                    self.RCR.page_source)
				self.callback_msg = f"订单状态: {self.order_status}"
				return False
		
		# 判断航班类型
		flight_type, fligth_type_list = self.DPR.parse_to_attributes('id', 'css',
		                                                             '[class="booking-details-table"] div[id]',
		                                                             self.RCR.page_source)
		if len(fligth_type_list) == 2:
			self.tripType = 2  # 回程
		elif len(fligth_type_list) == 1:
			self.tripType = 1  # 单程
		else:
			self.logger.info(self.tripType)
			self.callback_msg = f"航班信息解析失败: {fligth_type_list}"
			return False
		
		# 航班号
		flight_number, flight_number_list = self.DPR.parse_to_attributes('text', 'css',
		                                                                 '[id="ctl00_OptionalHeaderContent_radGridDepartTable_ctl00__0"] [class="left"]',
		                                                                 self.RCR.page_source)
		# 起飞到达目的地
		dep_arr_code, dep_arr_code_list = self.DPR.parse_to_attributes('text', 'css', '[class="rgHeader"][colspan="2"]',
		                                                               self.RCR.page_source)
		# 起飞时间, 到达时间
		departureTime, departureTime_list = self.DPR.parse_to_attributes('text', 'xpath',
		                                                                 '//*[@class="left itineraryCustom4"]//text()[3]',
		                                                                 self.RCR.page_source)

		for i in range(self.tripType):
			if i == 0:
				dep_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", departureTime_list[0])
				dep_time = self.BPR.parse_to_replace("\(.*?\)", "", dep_time)
				dep_time = self.DFR.format_to_transform(dep_time, "%d%b%Y,%H%M%p")
				dep_time = dep_time.strftime("%Y%m%d%H%M")
				arr_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", departureTime_list[1])
				arr_time = self.BPR.parse_to_replace("\(.*?\)", "", arr_time)
				arr_time = self.DFR.format_to_transform(arr_time, "%d%b%Y,%H%M%p")
				arr_time = arr_time.strftime("%Y%m%d%H%M")
				self.segments.append({
					"departureAircode": dep_arr_code_list[i].replace(' ', '').split('-')[0],
					"arrivalAircode": dep_arr_code_list[i].replace(' ', '').split('-')[1],
					"flightNum": flight_number_list[i].replace(' ', ''),
					"departureTime": dep_time,
					"arrivalTime": arr_time,
					"tripType": 1
				})
			elif i == 1:
				dep_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", departureTime_list[2])
				dep_time = self.BPR.parse_to_replace("\(.*?\)", "", dep_time)
				dep_time = self.DFR.format_to_transform(dep_time, "%d%b%Y,%H%M%p")
				dep_time = dep_time.strftime("%Y%m%d%H%M")
				arr_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", departureTime_list[3])
				arr_time = self.BPR.parse_to_replace("\(.*?\)", "", arr_time)
				arr_time = self.DFR.format_to_transform(arr_time, "%d%b%Y,%H%M%p")
				arr_time = arr_time.strftime("%Y%m%d%H%M")
				self.segments.append({
					"departureAircode": dep_arr_code_list[i].replace(' ', '').split('-')[0],
					"arrivalAircode": dep_arr_code_list[i].replace(' ', '').split('-')[1],
					"flightNum": flight_number_list[i].replace(' ', ''),
					"departureTime": dep_time,
					"arrivalTime": arr_time,
					"tripType": 2
				})
			else:
				self.callback_msg = "提取航段信息失败"
				return False

		return True

	def collect_to_segments(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		# # # 从详情页收集航段信息
		section, section_list = self.DPR.parse_to_attributes(
			"id", "css", "[id*=flightDisplayToggle_]>[id*=section_]:first-child", self.RCR.page_source)
		if section_list:
			for i in range(1, len(section_list) + 1):
				from_station, temp_list = self.DPR.parse_to_attributes(
					"text", "css",
					f"#flightDisplayToggle_{i}>#section_{i}:first-child>div:nth-child(2)>div:first-child",
					self.RCR.page_source
				)
				from_station = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", from_station)
				to_station, temp_list = self.DPR.parse_to_attributes(
					"text", "css",
					f"#flightDisplayToggle_{i}>#section_{i}:first-child>div:nth-child(2)>div:last-child",
					self.RCR.page_source
				)
				to_station = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", to_station)
				departure_time, temp_list = self.DPR.parse_to_attributes(
					"text", "css",
					f"#flightDisplayToggle_{i}>#section_{i}:first-child>div:nth-child(3)>span.left-text.grey1",
					self.RCR.page_source
				)
				departure_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", departure_time)
				departure_time = self.DFR.format_to_transform(departure_time, "%H%M,%d%b%Y")
				departure_time = departure_time.strftime("%Y%m%d%H%M")
				arrival_time, temp_list = self.DPR.parse_to_attributes(
					"text", "css",
					f"#flightDisplayToggle_{i}>#section_{i}:first-child>div:nth-child(3)>span.right-text.grey1",
					self.RCR.page_source
				)
				arrival_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", arrival_time)
				arrival_time = self.DFR.format_to_transform(arrival_time, "%H%M,%d%b%Y")
				arrival_time = arrival_time.strftime("%Y%m%d%H%M")
				flight_num, temp_list = self.DPR.parse_to_attributes(
					"text", "css",
					f"#flightDisplayToggle_{i}>#section_{i}:first-child>div:first-child>span",
					self.RCR.page_source
				)
				flight_num = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s", "", flight_num)
				self.segments.append({
					"departureAircode": from_station, "arrivalAircode": to_station, "flightNum": flight_num,
					"departureTime": departure_time, "arrivalTime": arrival_time, "tripType": 1
				})
			return True
		self.logger.info("航段超时或者错误(*>﹏<*)【segments】")
		self.callback_msg = "航段超时或者错误"
		return False
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		# # # 从详情页收集乘客信息，先判断是否有护照
		passengers, passengers_list = self.DPR.parse_to_attributes(
			"id", "css", "div[id*=passengerInputContainer]", self.RCR.page_source)
		
		for x in range(self.tripType):
			if passengers_list:
				for i in range(len(passengers_list)):
					sex, temp_list = self.DPR.parse_to_attributes(
						"value", "css",
						f"#CONTROLGROUP_OUTERTRAVELERCHANGE_CONTROLGROUPTRAVELERCHANGE_"
						f"PassengerInputTravelerChangeView_DropDownListTitle_{i}>option[selected]",
						self.RCR.page_source
					)
					child_sex, temp_list = self.DPR.parse_to_attributes(
						"value", "css",
						f"#CONTROLGROUP_OUTERTRAVELERCHANGE_CONTROLGROUPTRAVELERCHANGE_"
						f"PassengerInputTravelerChangeView_DropDownListGender_{i}>option[selected]",
						self.RCR.page_source
					)
					first_name, temp_list = self.DPR.parse_to_attributes(
						"value", "css",
						f"#CONTROLGROUP_OUTERTRAVELERCHANGE_CONTROLGROUPTRAVELERCHANGE_"
						f"PassengerInputTravelerChangeView_TextBoxFirstName_{i}",
						self.RCR.page_source
					)
					last_name, temp_list = self.DPR.parse_to_attributes(
						"value", "css",
						f"#CONTROLGROUP_OUTERTRAVELERCHANGE_CONTROLGROUPTRAVELERCHANGE_"
						f"PassengerInputTravelerChangeView_TextBoxLastName_{i}",
						self.RCR.page_source
					)
					birth_day, temp_list = self.DPR.parse_to_attributes(
						"value", "css",
						f"#CONTROLGROUP_OUTERTRAVELERCHANGE_CONTROLGROUPTRAVELERCHANGE_"
						f"PassengerInputTravelerChangeView_DropDownListBirthDateDay_{i}>option[selected]",
						self.RCR.page_source
					)
					if birth_day:
						birth_day = birth_day.zfill(2)
					birth_month, temp_list = self.DPR.parse_to_attributes(
						"value", "css",
						f"#CONTROLGROUP_OUTERTRAVELERCHANGE_CONTROLGROUPTRAVELERCHANGE_"
						f"PassengerInputTravelerChangeView_DropDownListBirthDateMonth_{i}>option[selected]",
						self.RCR.page_source
					)
					if birth_month:
						birth_month = birth_month.zfill(2)
					birth_year, temp_list = self.DPR.parse_to_attributes(
						"value", "css",
						f"#CONTROLGROUP_OUTERTRAVELERCHANGE_CONTROLGROUPTRAVELERCHANGE_"
						f"PassengerInputTravelerChangeView_DropDownListBirthDateYear_{i}>option[selected]",
						self.RCR.page_source
					)
					passengers_type = 0
					query_type, temp_list = self.DPR.parse_to_attributes(
						"value", "xpath", f"//a[@id='link_{i + 1}']//div[@class='tabText']//text()",
						self.RCR.page_source)
					if query_type and "Guest" in query_type:
						if sex == "MS":
							sex = "F"
						elif sex == "MR":
							sex = "M"
						passengers_type = 0
					elif query_type and "Child" in query_type:
						if child_sex == "2":
							sex = "F"
						elif child_sex == "1":
							sex = "M"
						passengers_type = 1
					
					appreciation = []
					flight, temp_list = self.DPR.parse_to_attributes(
						"text", "css", f"[class='target{i + 1} itinTable'] td[class='segmentContainer'] div[class='guest-detail-addon-caption']", self.temp_source)
					for ind, f in enumerate(temp_list):
						f = self.BPR.parse_to_clear(f)
						f = f.split('-')
						appreciation.append({
							"productType": "1",
							"departureAircode": f[0],
							"arrivalAircode": f[1],
							"detail": "",
							"tripType": ind + 1,
						})

					for num in range(self.tripType):
						self.baggage, temp_list = self.DPR.parse_to_attributes(
							"text", "css", f"[class='target{i + 1} itinTable'] td[class='segmentContainer']:nth-of-type({num + 1}) div",
							self.temp_source)

						for bag in temp_list:
							if "kg" in bag:
								bag, bag_list = self.BPR.parse_to_regex('.*?(\d{1,})', bag)
								for b in appreciation:
									b['detail'] = bag + "KG"

					for b in appreciation:
						if b.get('detail') == "":
							appreciation.remove(b)

					self.passengers.append({"passengerName": f"{last_name}/{first_name}",
					                        "passengerBirthday": birth_year + "-" + birth_month + "-" + birth_day,
					                        "identificationNumber": "", "cardType": "",
					                        "passengerNationality": "", "cardExpired": "", "passengerSex": sex,
					                        "passengerType": passengers_type,
					                        "auxArray": appreciation,
					                        "service_type": ""})
				return True
		self.callback_msg = "返回参数有误"
		return False
	
	def getssrdata(self, count: int = 0, max_count: int = 3):
		"""
        :param count:
        :param max_count:
        :return:
        """
		if count >= max_count:
			return False
		else:
			self.RCR.url = "https://k.airasia.com/ssr/getssrdata"
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "application/json",
				"Content-Type": "text/plain",
				"Host": "k.airasia.com",
				"Origin": "https://www.airasia.com",
				"Referer": "https://www.airasia.com/en/gb",
				"Channel_Hash": self.PSR.channel_id
			})
			self.RCR.post_data = {}
			if self.RCR.request_to_post("json", "json"):
				token_data = self.RCR.page_source.get('ssr_data')
				if token_data:
					if self.PSR.generate_to_bearer(token_data):
						return True
			
			self.callback_msg = "ssr_data 获取失败"
			return self.getssrdata(count + 1, max_count)
	
	def credentials(self, count: int = 0, max_count: int = 3):
		"""
        :param count:
        :param max_count:
        :return:
        """
		if count >= max_count:
			return False
		else:
			self.RCR.url = "https://ssor.airasia.com/sso/v2/authorization/by-credentials"
			self.RCR.param_data = (("clientId", self.client_id),)
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "application/json, text/plain, */*",
				"Content-Type": "application/json",
				"Host": "ssor.airasia.com",
				"Origin": "https://www.airasia.com",
				"Referer": "https://www.airasia.com/en/gb",
				"X-Api-Key": self.api_key,
			})
			self.RCR.post_data = {"username": self.CPR.username, "password": self.CPR.password}
			if self.RCR.request_to_post("json", "json"):
				
				self.data = str(self.RCR.page_source).replace(' ', '').replace('\'', '\"').replace('False', 'false')
				error_message, temp_list = self.BPR.parse_to_path("$.message", self.RCR.page_source)
				if error_message:
					self.logger.info(error_message)
					self.callback_msg = f"登录失败 {error_message}"
					return False
				self.access_token, temp_list = self.BPR.parse_to_path("$.accessToken", self.RCR.page_source)
				refresh_token, temp_list = self.BPR.parse_to_path("$.refreshToken", self.RCR.page_source)
				self.user_id, temp_list = self.BPR.parse_to_path("$.userId", self.RCR.page_source)
				self.loyalty_id, temp_list = self.BPR.parse_to_path("$.loyaltyId", self.RCR.page_source)
				return True
			
			self.callback_msg = f"登陆失败{self.RCR.url}"
			return self.credentials(count + 1, max_count)
	
	def users_data(self, count: int = 0, max_count: int = 3):
		"""
        :param count:
        :param max_count:
        :return:
        """
		if count >= max_count:
			return False
		else:
			self.RCR.url = f"https://ssor.airasia.com/um/v2/users/{self.user_id}"
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "application/json, text/plain, */*",
				"Host": "ssor.airasia.com",
				"Origin": "https://www.airasia.com",
				"Referer": "https://www.airasia.com/en/gb",
				"Authorization": self.access_token,
				"X-Api-Key": self.api_key,
				"X-AA-Client-Id": self.client_id
			})
			if self.RCR.request_to_get("json"):
				
				first_name, temp_list = self.BPR.parse_to_path("$.firstName", self.RCR.page_source)
				last_name, temp_list = self.BPR.parse_to_path("$.lastName", self.RCR.page_source)
				customer_number, temp_list = self.BPR.parse_to_path("$.navitaireCustomerNumber",
				                                                    self.RCR.page_source)
				if last_name and first_name and customer_number:
					self.RCR.set_to_cookies(False,
						[{"name": "memberLogin", "value": first_name, }])  # "domain": ".airasia.com", "path": "/"
					self.RCR.set_to_cookies(False,
						[{"name": "sso_userid", "value": self.loyalty_id, }])  # "domain": ".airasia.com", "path": "/"
					self.RCR.set_to_cookies(False,[{"name": "userLogin",
					                          "value": f"username={self.CPR.username}&firstnm={first_name}&lastnm={last_name}",
					                          }])  # "domain": ".airasia.com", "path": "/"
					self.RCR.set_to_cookies(False,
						[{"name": "_gtm_memberId",
						  "value": self.loyalty_id, }])  # "domain": ".airasia.com", "path": "/"
					self.logger.info("登录成功 | {},{},{}".format(last_name, first_name, customer_number))
					return True
			
			self.callback_msg = "登陆失败"
			return self.users_data(count + 1, max_count)
	
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