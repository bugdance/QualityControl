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
from collector.corpod_mirror import CorpODMirror
import random


class CorpODScraper(RequestWorker):
	"""OD采集器，全部首页质检
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
		self.CMR = CorpODMirror()  # OD镜像器
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
		self.user_agent, self.init_header = self.RCR.build_to_header("Chrome")
		# # # 质检流程
		if self.process_to_index():
			if self.process_to_login():
				if self.process_to_search():
					if self.process_to_segment():
						if self.process_to_detail():
							self.process_to_return()
							self.process_to_logout(max_count=self.retry_count)
							self.logger.removeHandler(self.handler)
							return self.callback_data
		# # # 错误返回。
		self.callback_data['msg'] = self.callback_msg
		# self.callback_data['msg'] = "解决问题中，请人工质检。"
		self.logger.info(self.callback_data)
		self.process_to_logout(max_count=self.retry_count)
		self.logger.removeHandler(self.handler)
		return self.callback_data
	
	def process_to_index(self) -> bool:
		"""首页查询航班流程
        :return:  bool
        """
		# # # 爬取首页
		self.RCR.url = "https://b2b.malindoair.com/MalindoAirAgentsPortal/Default.aspx"
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
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh-CN,zh;q=0.9',
		})
		if self.RCR.request_to_get():
			return True
		self.logger.info(f"首页超时或者错误(*>﹏<*)【{self.RCR.url}】")
		self.callback_msg = "首页超时或者错误"
		return False
	
	def process_to_login(self, count: int = 0, max_count: int = 2) -> bool:
		"""Login process. 登录过程。

		Args:
			count (int): 累计计数。
			max_count (int): 最大计数。

		Returns:
			bool
		"""
		verify_img_url, verify_img_url_list = self.DPR.parse_to_attributes(
			"src", "css", 'img[alt="Captcha"]', self.RCR.page_source)
		# # 提取验证码
		verify_code, temp_list = self.BPR.parse_to_regex('\=(\d{3,})', verify_img_url)
		view_state, temp_list = self.DPR.parse_to_attributes(
			"value", "css", 'input[id="__VIEWSTATE"]', self.RCR.page_source)
		view_rator, temp_list = self.DPR.parse_to_attributes(
			"value", "css", 'input[id="__VIEWSTATEGENERATOR"]', self.RCR.page_source)
		view_tion, temp_list = self.DPR.parse_to_attributes(
			"value", "css", 'input[id="__EVENTVALIDATION"]', self.RCR.page_source)
		self.RCR.url = "https://b2b.malindoair.com/MalindoAirAgentsPortal/Default.aspx"
		#  OD质检账户： QCYG-ZJ     Hthy@12345
		#  技术账户:    QCYG-ZJJS    Hthy@123456
		#               QCYG-JS      Hthy@12345
		account_list = ["QCYG-ZJJS|Hthy@123456", "QCYG-JS|Hthy@12345"]
		account = account_list[(random.randint(0, 1))].split("|")
		self.RCR.post_data = {
			'__EVENTTARGET': 'btnLogin',
			'__EVENTARGUMENT': '',
			'__VIEWSTATE': view_state,
			'__VIEWSTATEGENERATOR': view_rator,
			'__EVENTVALIDATION': view_tion,
			'txtLoginName': account[0],
			'txtPassword': account[1],
			'chkRememberMe': 'on',
			'CodeNumberTextBox': verify_code,
			'NameReqExtend_ClientState': '',
			'PasswordReqExtend_ClientState': ''
		}
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Origin': 'https://b2b.malindoair.com',
			'Upgrade-Insecure-Requests': '1',
			'Content-Type': 'application/x-www-form-urlencoded',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-User': '?1',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'same-origin',
			'Referer': 'https://b2b.malindoair.com/MalindoAirAgentsPortal/Default.aspx',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh-CN,zh;q=0.9',
		})
		if self.RCR.request_to_post(is_redirect=True):
			# 判断是否登录成功
			if "trLoginError" in self.RCR.page_source:
				error, temp_list = self.DPR.parse_to_attributes(
					"text", "css", 'tr [id="trLoginError"] td', self.RCR.page_source)
				error = self.BPR.parse_to_replace("\\r|\\t|\\n", "", error)
				self.logger.info(f"账号登录失败 【 {error} 】")
				self.callback_msg = f"账号登录失败【 {error} 】"
				return False
			else:
				return True
		self.logger.info("账号登录失败")
		self.callback_msg = "账号登录失败"
		return False
	
	# def pass_to_verify(self) -> bool:
	#     """
	#     验证码识别
	#     :return:
	#     """
	#     verify_img_url, verify_img_url_list = self.DPR.parse_as_attributes(
	#         "css", "src", 'img[alt="Captcha"]', self.RCR.page_source)
	#     self.RCR.url = "https://b2b.malindoair.com/MalindoAirAgentsPortal/" + verify_img_url
	#     self.RCR.param_data = None
	#     self.RCR.header = self.BFR.format_to_same(self.init_header)
	#     self.RCR.header.update({
	#         'Pragma': 'no-cache',
	#         'Sec-Fetch-Site': 'same-origin',
	#         'Accept-Encoding': 'gzip, deflate, br',
	#         'Accept-Language': 'zh-CN,zh;q=0.9',
	#         'Sec-Fetch-Mode': 'no-cors',
	#         'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
	#         'Cache-Control': 'no-cache',
	#         'Referer': 'https://b2b.malindoair.com/MalindoAirAgentsPortal/Default.aspx',
	#     })
	#     if self.RCR.request_to_get(page_type='content'):
	#         self.PSR.verify(self.RCR.page_source)
	#         return True
	
	def process_to_search(self):
		"""
        进行查询
        :return:
        """
		welcome, temp_list = self.DPR.parse_to_attributes(
			"action", "css", 'form[id="aspnetForm"]', self.RCR.page_source)
		manage_booking, temp_list = self.DPR.parse_to_attributes(
			"href", "css", 'td a[href*="RetrieveBooking"]', self.RCR.page_source)
		self.RCR.url = "https://b2b.malindoair.com" + manage_booking
		book_url = "https://b2b.malindoair.com" + manage_booking
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Upgrade-Insecure-Requests': '1',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-User': '?1',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'same-origin',
			'Referer': 'https://b2b.malindoair.com/MalindoAirAgentsPortal/Agents/' + welcome.replace('.', ''),
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh-CN,zh;q=0.9',
		})
		if self.RCR.request_to_get(is_redirect=True):
			view_state, temp_list = self.DPR.parse_to_attributes(
				"value", "css", 'input[id="__VIEWSTATE"]', self.RCR.page_source)
			rator, temp_list = self.DPR.parse_to_attributes(
				"value", "css", 'input[id="__VIEWSTATEGENERATOR"]', self.RCR.page_source)
			# 提交 pnr， 进行查询
			self.RCR.url = book_url
			self.RCR.post_data = {
				'__EVENTTARGET': 'lbRetrieve',
				'__EVENTARGUMENT': '',
				'__VIEWSTATE': view_state,
				'__VIEWSTATEGENERATOR': rator,
				'TextBox1': '',
				'txtBookingReference': self.CPR.record
			}
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				'Connection': 'keep-alive',
				'Pragma': 'no-cache',
				'Cache-Control': 'no-cache',
				'Origin': 'https://b2b.malindoair.com',
				'Upgrade-Insecure-Requests': '1',
				'Content-Type': 'application/x-www-form-urlencoded',
				'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
				'Sec-Fetch-Mode': 'navigate',
				'Sec-Fetch-User': '?1',
				'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
				'Sec-Fetch-Site': 'same-origin',
				'Referer': book_url,
				'Accept-Encoding': 'gzip, deflate, br',
				'Accept-Language': 'zh-CN,zh;q=0.9',
			})
			if self.RCR.request_to_post(is_redirect=True):
				return True
	
	def process_to_segment(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		if "errortext" in self.RCR.page_source:
			error, temp_list = self.DPR.parse_to_attributes(
				"text", "css", 'span[id="OutMessage"] li', self.RCR.page_source)
			self.logger.info(f"查不到订单 {error}")
			self.callback_msg = f"查不到订单 {error.split('.')[0]}"
			return False
		# 订单状态
		self.order_status, temp_list = self.DPR.parse_to_attributes(
			"text", "css", 'span[id="lblTimeLimit"]', self.RCR.page_source)
		if self.order_status == "Ticketed":
			self.order_status = "Confirmed"
		else:
			if not self.order_status:
				self.logger.info("订单状态获取失败 (*>﹏<*)【 order_status 】")
				self.callback_msg = f"订单状态获取失败"
				return False
		# 判断是否是往返
		segment, segment_list = self.DPR.parse_to_attributes(
			"text", "xpath", '//table[@id="FlightTable"]//tr[not(@id)]', self.RCR.page_source)
		for i in range(1, len(segment_list) + 1):
			# 航班号
			segment, segment_list = self.DPR.parse_to_attributes(
				"text", "css", f'div[class="FlightNumberInTable"] div:nth-child({i})', self.RCR.page_source)
			# 出发目的
			dep, dep_list = self.DPR.parse_to_attributes(
				"text", "xpath", f'//table[@id="FlightTable"]//tr[not(@id)][{i}]/td[2]//text()', self.RCR.page_source)
			dep_date = self.DFR.format_to_transform(" ".join([dep_list[2], dep_list[1].replace(', ', '')]),
			                                       '%d %b %Y %H:%M %a')
			arr, arr_list = self.DPR.parse_to_attributes(
				"text", "xpath", f'//table[@id="FlightTable"]//tr[not(@id)][{i}]/td[3]//text()', self.RCR.page_source)
			arr_date = self.DFR.format_to_transform(" ".join([arr_list[2], arr_list[1].replace(', ', '')]),
			                                       '%d %b %Y %H:%M %a')
			dep_code = ''
			arr_code = ''
			for coun_code in self.CMR._country_code:
				if dep == coun_code["cityName"]:
					dep_code = coun_code["cityCode"]
				if arr == coun_code["cityName"]:
					arr_code = coun_code["cityCode"]
			self.segments.append({
				"departureAircode": self.CPR.departure_code,
				"arrivalAircode": self.CPR.arrival_code,
				"flightNum": segment.replace(' ', ''),
				"departureTime": dep_date.strftime('%Y%m%d%H%M'),
				"arrivalTime": arr_date.strftime('%Y%m%d%H%M'),
				"tripType": i
			})
		return True
		#     self.callback_msg = f"查不到订单【{self.CPR.record}】"
		#     return False
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		# # # 从详情页收集乘客信息
		passengers, passengers_list = self.DPR.parse_to_attributes("text", "xpath",
		                                                           "//table[@id='PassengerTable']//tr[not(@id)]",
		                                                           self.RCR.page_source)
		for i in range(1, len(passengers_list) + 1):
			passengers, passengers_list = self.DPR.parse_to_attributes("text", "xpath",
			                                                           f"//table[@id='PassengerTable']//tr[not(@id)][{i}]/td/text()",
			                                                           self.RCR.page_source)
			passenger_data = passengers_list[1].split(' ')
			gender = ''  # 男： M ,  女： F
			passenger_type = ''  # 乘客类型， 0.成人， 1.儿童， 2.婴儿， -1.留学生
			if passenger_data[0] == "MS":  # 成人女
				gender = "F"
				passenger_type = 0
			elif passenger_data[0] == "MR":  # 成人男
				gender = "M"
				passenger_type = 0
			elif passenger_data[0] == "MISS":  # 儿童女
				gender = "F"
				passenger_type = 1
			else:  # 儿童男
				gender = "M"
				passenger_type = 1
			self.passengers.append({
				"passengerName": f"{passenger_data[2]}/{passenger_data[1]}",  # f"{last_name}/{first_name}"
				"passengerBirthday": "",
				"passengerSex": gender,
				"passengerType": passenger_type,
				"passengerNationality": "",
				"identificationNumber": "",
				"cardType": "", "cardExpired": "", "service_type": "",
				"auxArray": []
			})
		if self.luggage():
			luggage, luggage_list = self.DPR.parse_to_attributes("text", "xpath",
			                                                     "//table[@id='ctl00_BodyContentPlaceHolder_AncililaryTable']//tbody//td[5]/text()",
			                                                     self.RCR.page_source)
			# 遍历行李
			for i in range(len(luggage_list)):
				for num in self.segments:
					if "KG" in luggage_list[i]:
						self.passengers[i]['auxArray'].append(
							{
								"departureAircode": "",
								"arrivalAircode": "",
								"tripType": num['tripType'],
								"detail": luggage_list[i].replace('- ', ""),
								"productType": "1"
							}
						)
					else:
						self.passengers[i]['auxArray'] = []
				return True
		else:
			self.logger.info("获取行李失败 (*>﹏<*)【 luggage 】")
			self.callback_msg = "获取行李失败"
			return False
		# self.logger.info("乘客超时或者错误(*>﹏<*)【passengers】")
		# self.callback_msg = "乘客超时或者错误"
		# return False
	
	def luggage(self) -> bool:
		"""
        获取行李
        :return:
        """
		view_state, temp_list = self.DPR.parse_to_attributes(
			"value", "css", 'input[id="__VIEWSTATE"]', self.RCR.page_source)
		rator, temp_list = self.DPR.parse_to_attributes(
			"value", "css", 'input[id="__VIEWSTATEGENERATOR"]', self.RCR.page_source)
		self.RCR.url = "https://b2b.malindoair.com/MalindoAirAgentsMMB/MyBooking.aspx"
		self.RCR.post_data = {
			'__EVENTTARGET': 'lbAddServices',
			'__EVENTARGUMENT': '',
			'__VIEWSTATE': view_state,
			'__VIEWSTATEGENERATOR': rator
		}
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Origin': 'https://b2b.malindoair.com',
			'Upgrade-Insecure-Requests': '1',
			'Content-Type': 'application/x-www-form-urlencoded',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-User': '?1',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'same-origin',
			'Referer': 'https://b2b.malindoair.com/MalindoAirAgentsMMB/MyBooking.aspx',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh-CN,zh;q=0.9',
		})
		if self.RCR.request_to_post(is_redirect=True):
			return True
		else:
			self.logger.info("获取行李失败 (*>﹏<*)【 luggage 】")
			self.callback_msg = "获取行李失败"
			return False
	
	def process_to_logout(self, count: int = 0, max_count: int = 2) -> bool:
		"""Logout process. 退出过程。

		Args:
			count (int): 累计计数。
			max_count (int): 最大计数。

		Returns:
			bool
		"""
		self.RCR.url = "https://b2b.malindoair.com/MalindoAirAgentsPortal/Logout.aspx"
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Pragma': 'no-cache',
			'Cache-Control': 'no-cache',
			'Upgrade-Insecure-Requests': '1',
			'Sec-Fetch-Mode': 'navigate',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'none',
			'Accept-Encoding': 'gzip, deflate, br',
			'Accept-Language': 'zh-CN,zh;q=0.9',
		})
		if self.RCR.request_to_get(is_redirect=True):
			self.logger.info("账号退出登录成功")
			return True
		self.logger.info("账号退出登录失败")
		self.callback_msg = "账号退出登录失败"
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
