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
import paramiko  # ssh 连接Linux
import random
import time
from pyquery import PyQuery as pq


class Pers5JScraper(RequestWorker):
	"""5J采集器，全部首页质检
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
		
		self.RCR.retry_count = 5  # 重定向次数
		if self.get_proxy():
			# # 质检流程
			if self.process_to_index():
				if self.query_from_detail():
					if self.process_to_segment():
						if self.process_to_detail():
							self.process_to_return()
							self.logger.removeHandler(self.handler)
							return self.callback_data
				else:
					# self.RCR.session.cookies.clear()
					if self.process_to_login():
						if self.query_ticket_number():
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
	
	def get_proxy(self, count: int = 0, max_count: int = 3):
		"""
        判断代理，在规定时间段内使用
        :return:
        """
		if count >= max_count:
			return False
		else:
			# 判断当前时间是否在 00:00 - 05:30 时间段， 如果符合则使用代理，否则不使用
			current_time = self.DFR.format_to_now()
			now = time.strptime(current_time.strftime('%H%M'), "%H%M")  # 当前时间
			if time.strptime('0000', "%H%M") < now < time.strptime('2300', "%H%M"):
				
				self.RCR.timeout = 5
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
							self.RCR.timeout = 20
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
	
	def process_to_index(self, count: int = 0, max_count: int = 7) -> bool:
		"""首页查询航班流程
        :param count:  重试次数
        :param max_count:  重试最大次数
        :return:  bool
        """
		if count >= max_count:
			return False
		else:
			self.RCR.timeout = 5
			self.RCR.session.cookies.set(
				name="dtSa",
				value="true%7CC%7C-1%7C%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E2%80%8B%E8%88%AA%E7%8F%AD%E6%9C%BA%E7%A5%A8%20%2B%20%E9%85%92%E5%BA%97%E9%85%92%E5%BA%97%E6%82%A8%E6%83%B3%E5%8E%BB%E5%93%AA%E9%87%8C%EF%BC%9F%E5%BE%80%E8%BF%94%20%E5%8D%95%E7%A8%8B%20%E5%A4%9A%E4%B8%AA%E5%9F%8E%E5%B8%82%20Multi-city%20Description%20tool-tip.%20content%5Ec%20%E4%B8%80%E7%AC%94%E8%AE%A2%E5%8D%95%E5%B0%B1%E8%83%BD%E9%A2%84%E8%AE%A2%E4%BB%8E%E5%A4%9A%E4%B8%AA%E5%9F%8E%E5%B8%82%E5%87%BA%E5%8F%91%E7%9A%84%E8%88%AA%E7%8F%AD%E5%87%BA...%7C-%7C1579745306581%7C545097212_156%7Chttps%3A%2F%2Fwww.cebupacificair.com%2Fzh-cn%7C%E5%AE%BF%E5%8A%A1%E5%A4%AA%E5%B9%B3%E6%B4%8B%E8%88%AA%E7%A9%BA%E5%AE%98%E7%BD%91%E2%80%94%20Cebu%20Pacific%E6%88%90%E5%B0%B1%E6%82%A8%E7%9A%84%E8%8F%B2FUN%E4%B9%8B%E6%83%B3%EF%BC%81%7C1579745107898%7C%7C",
				# domain="book.cebupacificair.com",
				# path= "/"
			)
			self.RCR.session.cookies.set(
				name="dtCookie",
				value="1$86Q328KCUNK12VPTATT2OEO6SR9NOAUM|b471fd2b229e5313|1",
				# domain="book.cebupacificair.com",
				# path="/"
			)
			self.RCR.session.cookies.set(
				name="rxvt",
				value="1579747109124|1579745097219",
				# domain="book.cebupacificair.com",
				# path= "/"
			)
			self.RCR.session.cookies.set(
				name="dtPC",
				value="1$545097212_156h-vJDYKFMWLERRAKZXVQVSHXUQEUCITQQUR",
				# domain="book.cebupacificair.com",
				# path= "/"
			)
			self.RCR.session.cookies.set(
				name="bid_cap9kylkxexvqbwfljqctlwjpvukqvde",
				value="1dc1562e-22c1-4873-92ba-7575b5fb27b4",
				# domain="book.cebupacificair.com",
				# path= "/"
			)
			# # # # 爬取首页
			self.RCR.url = "https://book.cebupacificair.com"
			# self.RCR.url = "https://www.cebupacificair.com/en-us"
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				'authority': 'book.cebupacificair.com',
				'pragma': 'no-cache',
				'cache-control': 'no-cache',
				'upgrade-insecure-requests': '1',
				'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
				'sec-fetch-site': 'none',
				"Upgrade-Insecure-Requests": "1",
				"Host": "book.cebupacificair.com",
			})
			self.RCR.request_to_get()
			if self.verification():
				if self.get_proxy():
					return self.process_to_index(count + 1, max_count)
				else:
					return False
			# self.logger.info(self.RCR.page_source)
			self.verify_token, temp_list = self.DPR.parse_to_attributes(
				"value", "css", "#memberLoginForm input[name=__RequestVerificationToken]", self.RCR.page_source)
			
			if self.verify_token:
				self.RCR.set_to_cookies(False,
					[{"name": "__RequestVerificationToken",
					  "value": self.verify_token}])
			
			self.RCR.url = "https://book.cebupacificair.com/Manage/Retrieve"
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				'authority': 'book.cebupacificair.com',
				'pragma': 'no-cache',
				'cache-control': 'no-cache',
				'upgrade-insecure-requests': '1',
				'sec-fetch-mode': 'navigate',
				'sec-fetch-user': '?1',
				'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
				'sec-fetch-site': 'same-origin',
				"Upgrade-Insecure-Requests": "1",
				'referer': 'https://book.cebupacificair.com/',
			})
			if self.RCR.request_to_get():
			
				if len(self.RCR.page_source) < 100:
					self.logger.info(self.RCR.page_source)
					self.callback_msg = f"票号查询页面 返回失败 {self.RCR.url}"
					if self.get_proxy():
						return self.process_to_index(count + 1, max_count)
					else:
						return False
				self.verify_token, temp_list = self.DPR.parse_to_attributes(
					"value", "css", "#memberLoginForm input[name=__RequestVerificationToken]", self.RCR.page_source)
				
				if self.verify_token:
					return True
			
			self.logger.info("首页超时或者错误(*>﹏<*)【home】")
			self.callback_msg = "首页超时或者错误"
			if self.get_proxy():
				return self.process_to_index(count + 1, max_count)
			else:
				return False
	
	def query_from_detail(self, count: int = 0, max_count: int = 3) -> bool:
		"""查询详情信息流程
        :param count:  重试次数
        :param max_count:  重试最大次数
        :return:  bool
        """
		if count >= max_count:
			return False
		else:
			self.RCR.timeout = 10
			# # # # 请求详细页面
			self.RCR.url = "https://book.cebupacificair.com/Manage/DetermineRetrieve"
			self.RCR.post_data = {
				"recordLocator": self.CPR.record,
				"lastName": self.CPR.last_name
			}
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "*/*",
				"Host": "book.cebupacificair.com",
				"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
				"Origin": "https://book.cebupacificair.com",
				"x-dtpc": "-5$258464446_404h-vZUAMPVALPXEGSNDCTQWCUWSUKJXOLGFF",
				"Referer": "https://book.cebupacificair.com/Manage/Retrieve",
				"X-Requested-With": "XMLHttpRequest"
			})
			if self.RCR.request_to_post(is_redirect=True):  # 进行登陆
				
				self.RCR.url = "https://book.cebupacificair.com/Booking/RetrieveByEmailNames"
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.post_data = {
					"__RequestVerificationToken": self.verify_token,
					"cebRetrieveBooking.RecordLocator": self.CPR.record,
					"cebRetrieveBooking.LastName": self.CPR.last_name,
					"cebRetrieveBooking.EmailAddress": "",
					"bookingKey": "",
				}
				self.RCR.header.update({
					"Host": "book.cebupacificair.com",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
					"Content-Type": "application/x-www-form-urlencoded",
					"Origin": "https://book.cebupacificair.com",
					"Referer": "https://book.cebupacificair.com/Manage/Retrieve",
					"Upgrade-Insecure-Requests": "1",
				})
				if self.RCR.request_to_post():  # 进行查询
					# # # 解析跳转
					self.RCR.url = "https://book.cebupacificair.com/Manage"
					self.RCR.header = self.BFR.format_to_same(self.init_header)
					self.RCR.header.update({
						"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
						"Referer": "https://book.cebupacificair.com/Booking/RetrieveByEmailNames",
						"Upgrade-Insecure-Requests": "1",
						"Sec-Fetch-Mode": "navigate",
						"Sec-Fetch-Site": "same-origin",
					})
					if self.RCR.request_to_get():  # 返回票号信息页面
						# self.logger.info(self.RCR.page_source)
						if self.verification():  # 判断验证码
							if self.get_proxy():
								return self.query_from_detail(count + 1, max_count)
							else:
								return False
						if self.CPR.record in self.RCR.page_source:  # 判断页面是否有票号
							self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
							return True
						else:
							# 如果状态解析失败， 直接进行登录
							self.callback_msg = "返回不正常页面，或者票号有误"
							return False
			
			self.logger.info("详情超时或者错误(*>﹏<*)【detail】")
			self.callback_msg = "详情超时或者错误"
			if self.get_proxy():
				return self.query_from_detail(count + 1, max_count)
			else:
				return False
	
	def process_to_login(self, count: int = 0, max_count: int = 3):
		"""
        登录 5J
        :return:
        """
		if count >= max_count:
			return False
		else:
			
			self.RCR.timeout = 15
			# 判断接口账户是否符合要求, 如果不符合要求, 随机登陆账号, 否则直接使用接口提供的账号
			if self.CPR.username == "" or "@" not in self.CPR.username or self.CPR.password == "" \
					or "163.com" in self.CPR.username or "qq.com" in self.CPR.username:
				account = [
					{"username": 'olncptrjzpar@xuyangloveeat.ga', "password": '7232wslo$WLCS'},
					{"username": 'pzszzdfvcwra@xuyangloveeat.ga', "password": '0029inhj$NOEO'},
					{"username": 'mpwhxwyurhzl@xuyangloveeat.ga', "password": '0845skwx$PZDT'},
					{"username": 'lwopqpfdiuzh@xuyangloveeat.ga', "password": '8601iruf$AFLF'},
					{"username": 'ombvemkxopri@xuyangloveeat.ga', "password": '3207dozb$VPIZ'},
					{"username": 'sbeufugaskhw@xuyangloveeat.ga', "password": '4456ckpi$YUKP'},
					{"username": 'zssufmbjpwni@xuyangloveeat.ga', "password": '3015iscx$LDZU'},
					{"username": 'mqxswkntcbue@xuyangloveeat.ga', "password": '5887wcvf$TMFJ'},
					{"username": 'xmzhurvwxtrm@xuyangloveeat.ga', "password": '7392cdjj$ZQOO'},
					{"username": 'sheshou1111@126.com', "password": 'Pa$sw0rd71'},
					{"username": 'sheshou6666@126.com', "password": 'Pa$sw0rd71'},
					{"username": 'shehsou5555@126.com', "password": 'Pa$sw0rd71'},
					{"username": 'sheshou0000@126.com', "password": 'Pa$sw0rd71'},
					{"username": 'qicaisheshou4@126.com', "password": 'Pa$sw0rd71'},
				]
				log_account = account[random.randint(0, len(account) - 1)]
				self.CPR.username = log_account.get('username')
				self.CPR.password = log_account.get('password')
				self.logger.info(f'{self.CPR.username} | {self.CPR.password}')
				
			self.RCR.url = "https://book.cebupacificair.com/Member/RetrieveLogin"
			self.RCR.param_data = (
				("__RequestVerificationToken", self.verify_token),
				("cebMemberLogin.Username", self.CPR.username),
				("cebMemberLogin.Password", self.CPR.password),
				("bookingKey", "")
			)
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
				"Content-Type": "application/x-www-form-urlencoded",
				"Referer": "https://book.cebupacificair.com/Manage/Retrieve",
				"Sec-Fetch-Site": "same-origin",
				"Sec-Fetch-Mode": "navigate",
				"Sec-Fetch-User": "?1",
				"Upgrade-Insecure-Requests": "1",
				"origin": "https://book.cebupacificair.com",
			})
			if self.RCR.request_to_post(is_redirect=True):  # 进行登陆
				if "window.location='/Booking/Retrieve'" in str(self.RCR.page_source):
					self.RCR.url = "https://book.cebupacificair.com/Manage/Retrieve"
					self.RCR.param_data = None
					self.RCR.header = self.BFR.format_to_same(self.init_header)
					self.RCR.header.update({
						"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
						"Upgrade-Insecure-Requests": "1",
						"referer": "https://book.cebupacificair.com/zh-cn",
						'sec-fetch-mode': 'navigate',
						'authority': 'book.cebupacificair.com',
						"Host": "book.cebupacificair.com",
					})
					if self.RCR.request_to_get():
						error, error_list = self.DPR.parse_to_attributes('text', 'xpath',
						                                                 '//*[@class="error-details"]//text()',
						                                                 self.RCR.page_source)
						# self.logger.info(error_list)
						# self.logger.info(self.RCR.page_source)
						if "Invalid application id for domain book.cebupacificair.com" in self.RCR.page_source:
							if self.get_proxy():
								return self.process_to_login(count + 1, max_count)
							else:
								return False
						for i in error_list:
							if "account doesn't exist" in str(i):
								error = self.BPR.parse_to_replace("\\r|\\n|\\t|ERROR:|  ", "", i).split('.')
							elif "requires the GetGo member to login" in str(i):
								return self.process_to_login(count + 1, max_count)
							else:
								continue
						
						self.callback_msg = f"登录失败【 账户 {self.CPR.username} 可能被封 {error}】"
						return False
				
				if self.verification():
					if self.get_proxy():
						return self.process_to_login(count + 1, max_count)
					else:
						return False
				
				if self.mybookes_page():
					return True
				else:
					if self.get_proxy():
						return self.process_to_login(count + 1, max_count)
					else:
						return False
			
			else:
				if self.get_proxy():
					return self.process_to_login(count + 1, max_count)
				else:
					return False
	
	def query_ticket_number(self, count: int = 0, max_count: int = 3):
		"""
		
		Args:
			count: 
			max_count: 

		Returns:

		"""
		if count >= max_count:
			return False
		else:
			
			# 获取 提交航班是的参数
			self.verify_token, temp_list = self.DPR.parse_to_attributes(
				"value", "css", "#memberLoginForm input[name=__RequestVerificationToken]", self.RCR.page_source)
			if self.verify_token:
				retrieve, retrieve_list = self.DPR.parse_to_attributes(
					"value", "css", "input[name='retrieveBooking.IsBookingListRetrieve']", self.RCR.page_source)
				self.RCR.url = "https://book.cebupacificair.com/Manage/RetrieveInline"
				self.RCR.timeout = 15
				if retrieve:
					self.RCR.param_data = (
						("__RequestVerificationToken", self.verify_token),
						("retrieveBooking.IsBookingListRetrieve", retrieve),
						("id", self.CPR.record),
						("bookingKey", "")
					)
				# self.RCR.post_data = {
				#     "__RequestVerificationToken": self.verify_token,
				#     "retrieveBooking.IsBookingListRetrieve": 'true',
				#     "id": self.CPR.record,
				#     "bookingKey": ""
				# }
				else:
					self.RCR.param_data = (
						("__RequestVerificationToken", self.verify_token),
						("retrieveBooking.IsBookingListRetrieve", 'true'),
						("id", self.CPR.record),
						("bookingKey", "")
					)
				# self.RCR.post_data = {
				#     "__RequestVerificationToken": self.verify_token,
				#     "retrieveBooking.IsBookingListRetrieve": 'true',
				#     "id": self.CPR.record,
				#     "bookingKey": ""
				# }
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					"Referer": "https://book.cebupacificair.com/Member/MyBookings",
					"Sec-Fetch-Site": "same-origin",
					"Sec-Fetch-Mode": "navigate",
					"Sec-Fetch-User": "?1",
					"Origin": "https://book.cebupacificair.com",
					"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
				})
				if self.RCR.request_to_post():
					
					self.RCR.url = "https://book.cebupacificair.com/Manage"
					self.RCR.header = self.BFR.format_to_same(self.init_header)
					self.RCR.header.update({
						"Referer": "https://book.cebupacificair.com/Member/MyBookings",
						"Sec-Fetch-Site": "same-origin",
						"Sec-Fetch-Mode": "navigate",
						"Sec-Fetch-User": "?1"
					})
					if self.RCR.request_to_get(is_redirect=True):
						# self.logger.info(self.RCR.page_source)
						if self.verification():
							if self.get_proxy():
								return self.query_ticket_number(count + 1, max_count)
							else:
								return False
						if self.CPR.record in self.RCR.page_source:
							self.temp_source = self.BFR.format_to_same(self.RCR.page_source)
							return True
						else:
							# 如果状态解析失败， 直接进行登录
							self.callback_msg = "返回不正常页面，或者票号有误"
							return False
				else:
					if self.get_proxy():
						return self.query_ticket_number(count + 1, max_count)
					else:
						return False
	
	def process_to_segment(self, count: int = 0, max_count: int = 3) -> bool:
		"""收集航段信息
        :return:  bool
        """
		if self.verification():
			return False
		# self.logger.info(self.RCR.page_source)
		if len(self.temp_source) < 1000:
			self.callback_msg = "返回不正常页面，或者票号有误"
			return False
		# # # 获取订单状态
		self.order_status, temp_list = self.DPR.parse_to_attributes(
			"text", "css", "div.table.print-booking-details>div:nth-child(1) strong", self.temp_source)
		if self.order_status == 'CONFIRMED WITH PAYMENT DUE':
			self.order_status = "有未支付款项"
		elif self.order_status != 'CONFIRMED':
			self.order_status = "状态异常"
		# # # 从详情页收集航段信息
		flight_num, flight_num_list = self.DPR.parse_to_attributes(
			"value", "xpath",
			"//table[contains(@class, 'print-flight-details')]//tbody//p[@class='flight-number']/text()",
			self.temp_source)
		departure_code, dep_code_list = self.DPR.parse_to_attributes(
			"value", "xpath",
			"//table[contains(@class, 'print-flight-details')]/tbody/tr/td[2]/big[2]/text()",
			self.temp_source)
		arrival_code, arr_code_list = self.DPR.parse_to_attributes(
			"value", "xpath",
			"//table[contains(@class, 'print-flight-details')]/tbody/tr/td[4]/big[2]/text()",
			self.temp_source)
		# self.logger.info(flight_num_list)
		# 遍历航班号
		for nums in range(len(flight_num_list)):
			flight_num = self.BPR.parse_to_clear(flight_num_list[nums])
			
			# # # 解析时间
			from_date = ""
			to_date = ""
			temp_nums = 0
			if nums == 0:
				temp_nums = 1
			elif nums == 1:
				temp_nums = 3
			from_details, from_list = self.DPR.parse_to_attributes(
				"value", "xpath",
				f"//table[contains(@class, 'print-flight-details')]/tbody/tr[{temp_nums}]/td[2]/text()",
				self.temp_source)
			if not from_list:
				# flight_num_list
				self.logger.info(f"可能是中转航班 {flight_num_list}")
				self.callback_msg = f"可能是中转航班 {flight_num_list}"
				return False
			
			if from_list[-1]:
				from_details = self.BPR.parse_to_clear(from_list[-1])
			else:
				self.logger.info(from_list)
				return False
			from_details, temp_list = self.BPR.parse_to_regex("\.(.*)H", from_details)
			from_date = self.DFR.format_to_transform(from_details, '%d%b.%Y,%H%M')
			from_date = from_date.strftime("%Y%m%d%H%M")
			to_details, to_list = self.DPR.parse_to_attributes(
				"value", "xpath",
				f"//table[contains(@class, 'print-flight-details')]/tbody/tr[{temp_nums}]/td[4]/text()",
				self.RCR.page_source)
			to_details = self.BPR.parse_to_clear(to_list[-1])
			to_details, temp_list = self.BPR.parse_to_regex("\.(.*)H", to_details)
			to_date = self.DFR.format_to_transform(to_details, '%d%b.%Y,%H%M')
			to_date = to_date.strftime("%Y%m%d%H%M")
			self.segments.append({
				"departureAircode": dep_code_list[nums],
				"arrivalAircode": arr_code_list[nums],
				"flightNum": flight_num,
				"departureTime": from_date,
				"arrivalTime": to_date,
				"tripType": nums + 1
			})
		# self.logger.info(self.segments)
		return True
	
	def process_to_detail(self, count: int = 0, max_count: int = 3) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		if self.verification():
			return False
		# # # 从详情页收集乘客信息
		passengers, passengers_list = self.DPR.parse_to_attributes(
			"value", "xpath",
			"//table[contains(@class, 'print-guest-details')]/tbody//tr[not(contains(@class, 'table-hr'))]/td[1]/text()",
			self.RCR.page_source)
		if passengers_list:
			for i in passengers_list:
				appreciation = []
				age_type = 0
				sex = "M"
				passengers = self.BPR.parse_to_separate(i)
				passengers = passengers.split(" ")
				# if "Child" in
				if "Child" in i or "Adult" in i:
					if len(passengers) >= 5:
						last_name = passengers[-2]
						first_list = passengers[2:-2]
						first_name = ""
						for n in first_list:
							first_name += n + " "
						first_name = first_name.strip()
						if "Adult" in passengers[-1]:
							age_type = 0
							if passengers[1] == "Mr":
								sex = "M"
							else:
								sex = "F"
						elif "Child" in passengers[-1]:
							age_type = 1
							if passengers[1] == "Mstr":
								sex = "M"
							else:
								sex = "F"
						appreciation.append({
							# "detail": bagg,
							"productType": "1",
							"departureAircode": "",
							"arrivalAircode": "",
							# "tripType": self.segments[index_num].get("tripType"),
						})
						baggage, temp_list = self.DPR.parse_to_attributes(
							"text", "xpath",
							"//table[@class='table print-guest-details']/tbody//tr[not(contains(@class, 'table-hr'))][{}]/td[not(contains(@rowspan, '1'))]/text()".format(
								str(passengers_list.index(i) + 1)),
							str(self.RCR.page_source).replace("\n", ''))
						temp = []
						for i in temp_list:
							if "Kilos" in i:
								bag, bag_list = self.BPR.parse_to_regex('\,.*?(\d{1,})', i)
								temp.append(bag)
							else:
								continue
						if temp:
							appreciation[0]['detail'] = temp[0] + "KG"
						else:
							appreciation = []
						self.passengers.append({
							"passengerName": f"{last_name}/{first_name}", "passengerBirthday": "",
							"passengerSex": sex, "passengerType": age_type, "passengerNationality": "",
							"identificationNumber": "", "cardType": "", "cardExpired": "",
							"service_type": "", "auxArray": appreciation
						})
				else:
					continue
			
			for m in self.segments:
				for n in self.passengers:
					if n.get('auxArray'):
						for q in n.get('auxArray'):
							q['tripType'] = m.get('tripType')
					else:
						continue
			# 获取乘客生日信息， 不管成功还是失败，都返回失败。
			if not self.passengers_birthday():
				for i in self.passengers:
					i['passengerBirthday'] = ''
				return True
			return True
		self.logger.info("乘客超时或者错误(*>﹏<*)【passengers】")
		self.callback_msg = "乘客超时或者错误"
		return False
	
	def passengers_birthday(self, count: int = 0, max_count: int = 3):
		"""
        乘客生日
        :param count:
        :param max_count:
        :return:
        """
		if count >= max_count:
			return False
		else:
			self.process_to_index()
			self.RCR.url = "https://book.cebupacificair.com/Checkin/Retrieve"
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				'Upgrade-Insecure-Requests': '1',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
				'Host': 'book.cebupacificair.com',
				'Referer': 'https://book.cebupacificair.com/Manage/Retrieve',
			})
			if not self.RCR.request_to_get(is_redirect=True):
				if self.get_proxy():
					return self.passengers_birthday(count + 1, max_count)
				else:
					return False
			self.verify_token, temp_list = self.DPR.parse_to_attributes(
				"value", "css", "#memberLoginForm input[name=__RequestVerificationToken]", self.RCR.page_source)
			if self.verify_token:
				self.RCR.set_to_cookies(False,
					[{"name": "__RequestVerificationToken",
					  "value": self.verify_token
					  }])
			
			self.RCR.url = "https://book.cebupacificair.com/Checkin/RetrieveByLastName"
			self.RCR.param_data = None
			self.RCR.post_data = {
				"__RequestVerificationToken": self.verify_token,
				"cebCheckinRetrieveBooking.RecordLocator": self.CPR.record,
				"bookingKey": ""
			}
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				'Upgrade-Insecure-Requests': '1',
				'Content-Type': 'application/x-www-form-urlencoded',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
				'Host': 'book.cebupacificair.com',
				'Referer': 'https://book.cebupacificair.com/CheckIn/Retrieve',
				'Origin': 'https://book.cebupacificair.com',
			})
			if not self.RCR.request_to_post():
				if self.get_proxy():
					return self.passengers_birthday(count + 1, max_count)
				else:
					return False
			
			else:
				
				self.RCR.url = "https://book.cebupacificair.com/Checkin"
				self.RCR.param_data = None
				self.RCR.post_data = None
				self.RCR.header = self.BFR.format_to_same(self.init_header)
				self.RCR.header.update({
					'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
					'Referer': 'https://book.cebupacificair.com/Checkin/RetrieveByLastName',
				})
				if not self.RCR.request_to_get(is_redirect=True):
					if self.get_proxy():
						return self.passengers_birthday(count + 1, max_count)
					else:
						return False
				
				if self.verification():
					if self.get_proxy():
						return self.passengers_birthday(count + 1, max_count)
					else:
						return False
				
				# 提取生日信息
				html = pq(self.RCR.page_source)("div[id*='passportContainer'][class='detailsContainer ']")
				for i in self.passengers:
					name = i.get('passengerName').replace('/', ", ")
					for page in html.items():
						if name in str(page):
							birthday = page('[class="combined-date dob"]').attr('value')
							i['passengerBirthday'] = birthday
						else:
							continue
			return True
	
	def mybookes_page(self, count: int = 0, max_count: int = 3):
		"""判断登录后的页面是否为空"""
		if count >= max_count:
			return False
		else:
			self.RCR.url = "https://book.cebupacificair.com/Member/MyBookings"
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
				"Content-Type": "application/x-www-form-urlencoded",
				"Referer": "https://book.cebupacificair.com/Manage/Retrieve",
				"Sec-Fetch-Site": "same-origin",
				"Sec-Fetch-Mode": "navigate",
				"Upgrade-Insecure-Requests": "1",
				"referer": "https://book.cebupacificair.com/Manage/Retrieve"
			})
			if len(self.RCR.page_source) < 2:
				self.logger.info(f'''查询返回【 空页面 】【{self.RCR.url}】''')
				self.callback_msg = "查询或登录后，返回空页面"
				return False
			
			if self.RCR.request_to_get():
				user_name, user_name_list = self.DPR.parse_to_attributes('text', 'xpath',
				                                                         '//*[@id="hiGuestLink"]/text()',
				                                                         self.RCR.page_source)
				if "".join(user_name_list).replace(' ', '').replace('\n', ''):
					self.logger.info(
						"登录成功： " + f"{self.CPR.username}  " + "".join(user_name_list).replace(' ', '').replace('\n',
						                                                                                       '').replace(
							'\r', ''))
					self.RCR.timeout = 10
					
					if "__RequestVerificationToken" not in self.RCR.page_source:
						self.callback_msg = "登录后查询页面返回有误"
						self.logger.info(self.callback_msg)
						return self.mybookes_page(count + 1, max_count)
					else:
						return True
				else:
					self.callback_msg = f"登录失败【user name 未找到{user_name_list}】"
					return self.process_to_login(count + 1, max_count)
	
	def verification(self):
		"""
        判断是否有验证码
        :return:
        """
		if "data:image/png;base64" in self.RCR.page_source:
			verify_code, temp_list = self.DPR.parse_to_attributes(
				"src", "css", "[class='captcha-input'] img", self.RCR.page_source)
			self.logger.info(verify_code)
			self.callback_msg = "出现验证码"
			return True
		else:
			return False
	
	def connect_ssh(self, count: int = 0, max_count=2):
		"""
        连接拨号服务器
        """
		# 山东济南电信三型	yk1031k6	150.138.227.54:20248	9182c79ba7a4	t531181489925	123789
		# ip = "122.227.242.2"  user_name = "root"  port = 20480  pw = "5723e653956f"
		if count >= max_count:
			return False
		try:
			ip = "150.138.227.54"
			user_name = "root"
			port = 20248
			pw = "9182c79ba7a4"
			self.ssh = paramiko.SSHClient()
			self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			self.ssh.connect(hostname=ip, port=port, username=user_name, password=pw, timeout=15)
		
		except Exception as ex:
			self.logger.info(ex)
			return self.connect_ssh(count + 1, max_count)
	
	def get_dial_proxy(self, count: int = 0, max_count: int = 2):
		"""
        拨号并获取 IP
        :param count:
        :param max_count:
        :return:
        """
		if count >= max_count:
			return False
		try:
			self.connect_ssh()
			# 切换国外代理， 执行 adsl-stop, adsl-start, pppoe-status 命令，获取结果
			command = ['adsl-stop', 'adsl-start', "pppoe-status | sed -n '/inet/'p"]
			nums = 0  # 重试次数
			stdin, stdout, stderr = self.ssh.exec_command(command=command[0], get_pty=True, timeout=60)
			stdin, stdout, stderr = self.ssh.exec_command(command=command[1], get_pty=True, timeout=60)
			time.sleep(8)
			while True:
				stdin, stdout, stderr = self.ssh.exec_command(command=command[2], get_pty=True, timeout=60)
				out = str(stdout.readlines()).replace(' ', '')
				self.proxy_ip, temp = self.BPR.parse_to_regex('inet(.*?)peer', str(out.replace(' ', '')))
				if self.proxy_ip:
					self.ssh.close()
					# self.proxys = "http://yunku:123@" + self.proxy_ip + ":" + "3138"
					self.proxys = "http://yunku:123@" + self.proxy_ip + ":" + "3138"
					
					self.RCR.set_to_proxy(enable_proxy=True, address=self.proxys)
					return True
				else:
					# 重试次数
					if nums < 4:
						time.sleep(1)
						nums += 1
						continue
					else:
						self.logger.info("拨号失败")
						return False
		
		except Exception as ex:
			self.logger.info(ex)
			return self.get_dial_proxy(count + 1, max_count)
	
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