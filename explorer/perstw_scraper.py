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
from booster.callback_formatter import CallBackFormatter
from booster.date_formatter import DateFormatter
from booster.dom_parser import DomParser

from fortifier.perstw_refactor import BPRefactor, CPRefactor
import time
import random


class PersTWScraper(RequestWorker):
	"""TT采集器

    """
	
	def __init__(self):
		RequestWorker.__init__(self)
		self.RCR = RequestCrawler()  # 请求爬行器。
		self.AFR = AESFormatter()  # AES格式器。
		self.BFR = BasicFormatter()  # 基础格式器。
		self.BPR = BPRefactor()  # 基础解析器。
		self.CFR = CallBackFormatter()  # 回调格式器。
		self.CPR = CPRefactor(False)  # 接入解析器。
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
		
		if self.get_proxy():
			if self.process_to_index():
				if self.process_to_search():
					if self.process_to_login():
						if self.get_post_data():
							if self.get_flight_detail():
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
	
	def get_proxy(self, count: int = 0, max_count: int = 4):
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
				service_type = ["4", "4", "4"]
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
	
	def process_to_index(self) -> bool:
		"""首页查询航班流程
        :return:  bool
        """
		# # # 爬取首页
		self.RCR.url = "https://www.twayair.com/app/main"
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
		if self.RCR.request_to_get(is_redirect=True):
			if 'Your IP address' in self.RCR.page_source:
				self.logger.info("配置代理失效(*>﹏<*)")
				return False
			return True
		return False
	
	def process_to_search(self) -> bool:
		"""查询预定流程
        :return:  bool
        """
		# # # 爬取预定页面
		self.RCR.url = "https://www.twayair.com/app/reservation/reservationList"
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Sec-Fetch-Site': 'same-origin',
			'Referer': 'https://www.twayair.com/app/main',
		})
		
		if self.RCR.request_to_get(is_redirect=True):
			if 'Your IP address' in self.RCR.page_source:
				self.logger.info("配置代理失效(*>﹏<*)")
				return False
			return True
		return False
	
	def process_to_login(self) -> bool:
		"""查询登录信息流程
        :return:  bool
        """
		# # # 爬取登录页面
		self.RCR.url = "https://www.twayair.com/app/reservation/searchMemberBooking"
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Referer': 'https://www.twayair.com/app/login/memberLogin?returnUrl=/app/reservation/reservationList',
		})
		if self.RCR.request_to_get():
			if 'Your IP address' in self.RCR.page_source:
				self.logger.info("配置代理失效(*>﹏<*)")
				return False
			return True
		return False
	
	def get_post_data(self) -> bool:
		"""获取请求参数
        :return: bool
        """
		self.RCR.url = "https://www.twayair.com/ajax/reservation/pnrValidate"
		lastNameLIst = []
		firstNameList = []
		for i in self.CPR.passenger_name_list:
			lastNameLIst.append(i['last_name'])
		for m in self.CPR.passenger_name_list:
			firstNameList.append(m['first_name'])
		
		self.RCR.param_data = (
			('pnrNumber', self.CPR.record),
			('lastName', lastNameLIst),
			('firstName', firstNameList),
			('isCheckin', 'false'),
			('isGuest', 'false'),
			('boardingDay', 'undefinedundefinedundefined'),
		)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Referer': 'https://www.twayair.com/app/reservation/searchMemberBooking',
		})
		if self.RCR.request_to_get():
			try:
				self.encPnrNumber = self.BPR.parse_to_dict(self.RCR.page_source)['data']['encPnrNumber']
				self.encGuestId = self.BPR.parse_to_dict(self.RCR.page_source)['data']['encGuestId']
				if self.encPnrNumber and self.encGuestId:
					return True
			except Exception as ex:
				self.logger.info(f"解析post_data数据失败 确认是否传入正确参数(*>﹏<*)")
		
		else:
			self.logger.info(f"解析post_data数据失败 确认是否传入正确参数(*>﹏<*)")
			return False
	
	def get_flight_detail(self) -> bool:
		"""获取数据
        :return: bool
        """
		self.RCR.url = "https://www.twayair.com/app/reservation/reservationDetail"
		self.RCR.param_data = (
			('encPnrNumber', self.encPnrNumber),
			('encGuestId', self.encGuestId),
		)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Referer': 'https://www.twayair.com/app/reservation/searchMemberBooking',
			'Cache-Control': 'max-age=0',
		})
		if self.RCR.request_to_get():
			return True
		return False
	
	def process_to_segment(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		self.order_status, template = self.DPR.parse_to_attributes('text', 'css', '.reservation_section > ul:nth-child('
		                                                                          '1) > li:nth-child(1) > div:nth-child(1) > span:nth-child(2) > i:nth-child(1)',
		                                                           self.RCR.page_source)
		if not self.order_status:
			self.order_status, template = self.DPR.parse_to_attributes('text', 'css',
			                                                           '.reservation_section > ul:nth-child('
			                                                           '1) > li:nth-child(1) > div:nth-child(1) > span:nth-child(2)',
			                                                           self.RCR.page_source)
			if self.order_status:
				self.order_status = self.BPR.parse_to_separate(self.order_status)
				self.logger.info(self.order_status)
				self.callback_msg = self.order_status
				return False
			else:
				self.logger.info("获取航班状态失败")
				self.callback_msg = "获取航班状态失败"
				return False
		
		# # # 从详情页收集航段信息
		flight_detail, fd_list = self.DPR.parse_to_attributes('class', 'css', '.reservation_section ul li '
		                                                                      'div.section_tit', self.RCR.page_source)
		for i in range(len(fd_list)):
			
			dep_code, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                                   f'.reservation_section > ul:nth-child(1) > li:nth-child({i + 1}) > dl:nth-child(2) > dd:nth-child(2) > div:nth-child(1) > div:nth-child(1) > strong:nth-child(1)',
			                                                   self.RCR.page_source)
			trip_type, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                                    f'.reservation_section > ul:nth-child(1) > li:nth-child({i + 1}) > div:nth-child(1) > span:nth-child(1)',
			                                                    self.RCR.page_source)
			if trip_type == '区段1':
				trip_type = 1
			else:
				trip_type = 2
			arr_code, temp_list = self.DPR.parse_to_attributes('text', 'css', f'.reservation_section > ul:nth-child(1) '
			                                                                  f'> li:nth-child({i + 1}) > dl:nth-child(2) > dd:nth-child(2) > div:nth-child(1) > div:nth-child(3) > strong:nth-child(1)',
			                                                   self.RCR.page_source)
			flight_num, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                                     f'.reservation_section > ul:nth-child(1) > li:nth-child({i + 1}) > dl:nth-child(2) > dd:nth-child(2) > div:nth-child(1) > div:nth-child(2) > p:nth-child(2) > a:nth-child(1)',
			                                                     self.RCR.page_source)
			time, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                               f'.reservation_section > ul:nth-child(1) > li:nth-child({i + 1}) > dl:nth-child(2) > dd:nth-child(2) > div:nth-child(1) > div:nth-child(2) > p:nth-child(1)',
			                                               self.RCR.page_source)
			date, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                               f'.reservation_section > ul:nth-child(1) > li:nth-child({i + 1}) > dl:nth-child(2) > dt:nth-child(1) > span:nth-child(1)',
			                                               self.RCR.page_source)
			time = self.BPR.parse_to_replace('\t|\n| ', '', time)
			time_list = self.BPR.parse_as_split('[~|//]', time)
			dep_time = self.DFR.format_to_transform(time_list[0], "%H:%M")
			arr_time = self.DFR.format_to_transform(time_list[1], "%H:%M")
			from_date = self.DFR.format_to_transform(date[:-5], '%Y-%m-%d').strftime('%Y%m%d') + dep_time.strftime(
				'%H%M')
			to_date = self.DFR.format_to_transform(date[:-5], '%Y-%m-%d').strftime('%Y%m%d') + arr_time.strftime('%H%M')
			if arr_time < dep_time:
				arr_date = self.DFR.format_to_transform(date[:-5], '%Y-%m-%d')
				arr_date = self.DFR.format_to_custom(arr_date, custom_days=1).strftime('%Y%m%d')
				to_date = arr_date + arr_time.strftime("%H%M")
			self.segments.append({
				"departureAircode": dep_code, "arrivalAircode": arr_code,
				"flightNum": flight_num, "departureTime": from_date,
				"arrivalTime": to_date, "tripType": trip_type
			})
		return True
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		# # # 从详情页收集乘客信息
		passenger, psg_list = self.DPR.parse_to_attributes('class', 'css', '.passenger_list ul li a',
		                                                   self.RCR.page_source)
		for i in range(len(psg_list)):
			name, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                               f'.passenger_list > ul:nth-child(1) > li:nth-child({i + 1}) > a:nth-child(1) > span:nth-child(2)',
			                                               self.RCR.page_source)
			pas_type, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                                   f'.passenger_list > ul:nth-child(1) > li:nth-child({i + 1}) > a:nth-child(1) > span:nth-child(3)',
			                                                   self.RCR.page_source)
			birthday, temp_list = self.DPR.parse_to_attributes('text', 'css',
			                                                   f'.passenger_list > ul:nth-child(1) > li:nth-child({i + 1}) > a:nth-child(1) > span:nth-child(4)',
			                                                   self.RCR.page_source)
			gender, temp_list = self.DPR.parse_to_attributes('class', 'css',
			                                                 f'.passenger_list > ul:nth-child(1) > li:nth-child({i + 1}) > a:nth-child(1) > span:nth-child(1)',
			                                                 self.RCR.page_source)
			gender = gender[-1]
			if pas_type == '成人':
				pas_type = 0
			elif pas_type == "儿童":
				pas_type = 1
			else:
				pas_type = 3
			
			self.passengers.append({
				"passengerName": name, "passengerBirthday": birthday,
				"passengerSex": gender, "passengerType": pas_type, "passengerNationality": "",
				"identificationNumber": "", "cardType": "", "cardExpired": "",
				"service_type": ""
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

