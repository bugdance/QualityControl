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


class CorpUOScraper(RequestWorker):
	"""UO采集器，全部首页质检
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
	
	def process_to_index(self) -> bool:
		"""首页查询航班流程
        :return:  bool
        """
		# # # 请求登录首页
		self.RCR.url = "https://www.hkexpress.com/zh-hk/agencies/login"
		self.RCR.param_data = None
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			'Upgrade-Insecure-Requests': '1',
			'Sec-Fetch-Mode': 'navigate',
			'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
			'Sec-Fetch-Site': 'none',
		})
		if self.RCR.request_to_get():
			# 获取 apiKey
			self.RCR.url = "https://www.hkexpress.com/Angular/common.chunk.js?v=C7uSMnpwfkwUY8d69asQ5A=="
			self.RCR.param_data = None
			self.RCR.header = self.BFR.format_to_same(self.init_header)
			self.RCR.header.update({
				'sec-fetch-mode': 'no-cors',
				'accept': '*/*',
				'referer': 'https://www.hkexpress.com/zh-hk/agencies/login',
				'authority': 'www.hkexpress.com',
				'sec-fetch-site': 'same-origin',
			})
			if self.RCR.request_to_get():
				# header 中 apikey
				self.apikey, temp_list = self.BPR.parse_to_regex(r'apiKey\:\"(.*?)\"', self.RCR.page_source)
				if not self.apikey:
					self.logger.info(f"apiKey 获取失败 {temp_list} ")
					self.callback_msg = "首页返回有误"
					return False
				
				return True
		self.logger.info(f"首页超时或者错误(*>﹏<*)【{self.RCR.url}】")
		self.callback_msg = "首页超时或者错误"
		return False
	
	def process_to_login(self, count: int = 0, max_count: int = 2):
		"""
        进行登录 UO
        :return:
        """
		if count >= max_count:
			return False
		
		self.RCR.url = "https://booking-api.hkexpress.com/api/v1.0/agent"
		self.RCR.post_data = str({"username": self.CPR.username,
		                          "password": self.CPR.password,
		                          "loginType": "Agent"
		                          }).replace('\'', '\"')
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "application/json, text/plain, */*",
			"Content-Type": "application/json; charset=UTF-8",
			"Host": "booking-api.hkexpress.com",
			"Referer": "https://booking.hkexpress.com/zh-cn/agencies/login/",
			"Origin": "https://booking.hkexpress.com",
			"apiKey": self.apikey,
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-site",
		})
		self.RCR.timeout = 30
		if self.RCR.request_to_post(page_type='json'):
			if self.RCR.page_source.get('lastName') == "LIU":
				return True
			else:
				self.logger.info("登录失败 | 返回结果找不到用户信息")
				self.callback_msg = "登录失败 | 返回结果找不到用户信息"
				return False
		else:
			self.logger.info(f"登录失败 | 请求异常")
			self.callback_msg = "登录失败 | 请求异常"
			return self.process_to_login(count + 1, max_count)
	
	def process_to_search(self, count: int = 0, max_count: int = 2):
		"""
        提交 票号 进行查询
        :return:
        """
		if count >= max_count:
			return False
		self.RCR.url = "https://booking-api.hkexpress.com/api/v1.0/MemberBooking"
		now_date = self.DFR.format_to_now().strftime('%Y-%m-%d')  # 当前时间
		self.RCR.param_data = (
			('beginDate', self.DFR.format_to_now(custom_days=-180).strftime('%Y-%m-%d')),
			# 当前日期推迟半年
			('endDate', self.DFR.format_to_now(custom_days=1).strftime('%Y-%m-%d')),  # 当前日期
			('recordLocator', self.CPR.record),
		)
		self.RCR.header = self.BFR.format_to_same(self.init_header)
		self.RCR.header.update({
			"Accept": "application/json, text/plain, */*",
			"Host": "booking-api.hkexpress.com",
			"Referer": "https://booking.hkexpress.com/zh-HK/agencies/agencybookings",
			"Origin": 'https://booking.hkexpress.com',
			"apiKey": self.apikey,
		})
		if self.RCR.request_to_get('json'):
			# 判断返回是否成功，如果不成功重试一次
			response_status, temp_list = self.BPR.parse_to_path('$.success', self.RCR.page_source)
			if not response_status:
				return self.process_to_search(count + 1, max_count)
			flightInfo, flightInfo_list = self.BPR.parse_to_path('$.flightInfoByCustomerResponses',
			                                                     self.RCR.page_source)
			if not flightInfo:
				self.logger.info(f"未查到订单可能已经飞走{flightInfo_list}")
				self.callback_msg = f"未查到订单可能已经飞走{flightInfo_list}"
				return False
			# 判断机票状态， 机票是否付款
			self.order_status, temp_list = self.BPR.parse_to_path('$..bookingStatus', self.RCR.page_source)
			currencyCode, temp_list = self.BPR.parse_to_path('$..bookingStatus', self.RCR.page_source)
			balance, temp_list = self.BPR.parse_to_path('$..balanceDueByFlight', self.RCR.page_source)
			if int(balance) > 0:
				self.logger.info(f"有未付款项，支付金额 【{balance} {currencyCode}】")
				self.callback_msg = f"有未付款项，支付金额 【{balance} {currencyCode}】"
				return False
			self.RCR.url = "https://booking-api.hkexpress.com/api/v1.0/booking/ManageBookingLogin"
			self.RCR.param_data = (
				('recordLocator', self.CPR.record),
				('lastName', self.CPR.last_name),
			)
			self.RCR.header.update({
				"Accept": "application/json, text/plain, */*",
				"Host": "booking-api.hkexpress.com",
				"Referer": "https://booking.hkexpress.com/zh-HK/agencies/agencybookings",
				"Origin": 'https://booking.hkexpress.com',
				"apiKey": self.apikey,
			})
			if self.RCR.request_to_get('json'):
				return True
		else:
			self.logger.info(f"票号查询失败【{self.RCR.url}】")
			self.callback_msg = "详票号查询失败"
			return False
	
	def process_to_segment(self) -> bool:
		"""收集航段信息
        :return:  bool
        """
		# 判断页面是否存在 PNR
		pnr, temp_html = self.BPR.parse_to_path(path_syntax='$..recordLocator', source_data=self.RCR.page_source)
		if pnr:
			html, temp_html = self.BPR.parse_to_path(path_syntax='$..journeyType', source_data=self.RCR.page_source)
			for i in temp_html:
				if i == "Outbound":
					trip_type = 1  # 去程
				elif i == "Return":
					trip_type = 2  # 回程
				else:
					trip_type = ""
				# 出发到达三字码
				flight_information, flight_information_list = self.BPR.parse_to_path(
					path_syntax=f'$.journeys[{temp_html.index(i)}]',
					source_data=self.RCR.page_source)
				dep_code, code_list = self.BPR.parse_to_path(
					path_syntax=f'$.originIata', source_data=flight_information)
				arr_code, code_list = self.BPR.parse_to_path(
					path_syntax=f'$.destinationIata', source_data=flight_information)
				# 出发日期
				from_date, date_list = self.BPR.parse_to_path(
					path_syntax=f'$.departureDate', source_data=flight_information)
				from_date = self.DFR.format_to_transform(from_date, "%Y-%m-%dT%H:%M:%S").strftime("%Y%m%d%H%M")
				# 到达日期
				to_date, date_list = self.BPR.parse_to_path(
					path_syntax=f'$.arrivalDate', source_data=flight_information)
				to_date = self.DFR.format_to_transform(to_date, "%Y-%m-%dT%H:%M:%S").strftime("%Y%m%d%H%M")
				# 航班号
				flight_num, flight_num_list = self.BPR.parse_to_path(
					path_syntax=f'$..flightNumber', source_data=flight_information)
				carrierCode, carrierCode_list = self.BPR.parse_to_path(
					path_syntax=f'$..carrierCode', source_data=flight_information)
				self.segments.append({
					"departureAircode": dep_code,
					"arrivalAircode": arr_code,
					"flightNum": carrierCode + flight_num.replace(' ', ''),
					"departureTime": from_date,
					"arrivalTime": to_date,
					"tripType": trip_type
				})
			return True

		self.logger.info(f"航班信息有误【process_to_segment】")
		self.callback_msg = "质检失败, 航班信息有误"
		return False
	
	def process_to_detail(self) -> bool:
		"""收集乘客信息
        :return:  bool
        """
		# 航班数据
		flight_data = self.RCR.page_source
		# 乘客信息
		information, information_list = self.BPR.parse_to_path(
			path_syntax=f'$.passengers', source_data=flight_data)
		# 航班信息
		journey_type, journey_type_list = self.BPR.parse_to_path(
			path_syntax='$.journeys', source_data=flight_data)

		# 拼接乘客返回信息
		for i in information:
			first_name, first_name_list = self.BPR.parse_to_path(
				path_syntax=f'$.firstName', source_data=i)
			last_name, last_name_list = self.BPR.parse_to_path(
				path_syntax=f'$.lastName', source_data=i)
			# 乘客生日
			birthday, birthday_list, = self.BPR.parse_to_path(
				path_syntax=f'$.dateOfBirth', source_data=i)
			birthday = self.DFR.format_to_transform(birthday, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
			# 性别
			gender, gender_list = self.BPR.parse_to_path(
				path_syntax=f'$.gender', source_data=i)
			if gender == "Female":
				gender = 'F'
			elif gender == "Male":
				gender = 'M'
			# 乘客类型
			"passengerStatusType"
			passenger_type, passenger_type_list = self.BPR.parse_to_path(
				path_syntax=f'$.passengerStatusType', source_data=i)
			if passenger_type == "Active":
				passenger_type = 0
			elif passenger_type == "":
				passenger_type = 1
			nationality, nationality_list = self.BPR.parse_to_path(
				path_syntax=f'$.nationality', source_data=i)
			# 证件号
			number, number_temp = self.BPR.parse_to_path(
				path_syntax=f'$..number', source_data=i)
			# cardExpired 证件有效日期
			card_expired, card_expired_temp = self.BPR.parse_to_path(
				path_syntax=f'$..expirationDate', source_data=i)
			# 乘客服务信心
			auxiliary_service,  paxAncillaries = self.BPR.parse_to_path(
				path_syntax=f'$.paxAncillaries', source_data=i)

			aux = []
			for service in auxiliary_service:
				for journey in journey_type:
					if service.get('segmentId')  == journey.get('journeyId') and "PB" in service.get('code'):

						detail = service.get('bookingFeeId').replace('P', '') + "KG"

						trip_type = 0
						if journey.get('journeyType') == "Outbound":
							trip_type = 1
						elif journey.get('journeyType') == "Return":
							trip_type = 2
						aux.append(
							{
								"departureAircode": journey.get('originIata'),
								"arrivalAircode": journey.get('destinationIata'),
								"tripType": trip_type,
								"detail": detail,   # 行李
								"productType": "1"  # 增值服务类型
							}
						)
			self.passengers.append({
				"passengerName": f"{last_name}/{first_name}",
				"passengerBirthday": birthday,  # 乘客生日
				"passengerSex": gender,         # 乘客性别
				"passengerType": passenger_type,      # 乘客类型， 成人 0，  儿童 1
				"passengerNationality": nationality,  # 乘客国籍
				"identificationNumber": number,       # 证件号码
				"cardType": "",  # 证件类型
				"cardExpired": card_expired.split('T')[0],  # 证件有效日期
				"service_type": "",  # 增值服务类型
				"auxArray": aux      # 行李数据
			})

		# # 获取行李数据
		# self.RCR.url = "https://booking-api.hkexpress.com/api/v1.0/booking/availableAncillaries?AncillaryTypes=Meal,Baggage,Oversize,Priority"
		# self.RCR.post_data = None
		# self.RCR.param_data = None
		# self.RCR.header = self.BFR.format_to_same(self.init_header)
		# self.RCR.header.update({
		# 	"Accept": "application/json, text/plain, */*",
		# 	"Content-Type": "application/json; charset=UTF-8",
		# 	"Host": "booking-api.hkexpress.com",
		# 	"Origin": "https://booking.hkexpress.com",
		# 	"apiKey": "1a739d42f96658378a0ac7804fefdb2ebd649182e4971c99a3edd1e949277270",
		# 	"Upgrade-Insecure-Requests": "1",
		# 	'Referer': 'https://booking.hkexpress.com/zh-HK/manage/ancillaries',
		# })
		# if not self.RCR.request_to_get('json'):
		# 	self.logger.info(f"行李获取失败 | {self.RCR.url}")
		# 	self.callback_msg = "行李获取失败"
		# 	return False
		# # 行李
		# detail, detail_list = self.BPR.parse_to_path(
		# 	path_syntax=f'$..confirmed', source_data=self.RCR.page_source)
		# n = None
		# for i in detail_list:
		# 	if i:
		# 		n = detail_list.index(i)
		# 	else:
		# 		continue
		# if n:
		# 	baggage, baggage_list = self.BPR.parse_to_path(
		# 		path_syntax=f'$..feeCode', source_data=self.RCR.page_source)
		# 	detail = baggage_list[n].replace('P', '') + "KG"
		# else:
		# 	detail = ''
		# for i in information:
		# 	if "Return" in journey_type_list:
		# 		trip_type = information.index(i) + 1
		# 	else:
		# 		trip_type = 1
		# 	first_name, first_name_list = self.BPR.parse_to_path(
		# 		path_syntax=f'$.firstName', source_data=i)
		# 	last_name, last_name_list = self.BPR.parse_to_path(
		# 		path_syntax=f'$.lastName', source_data=i)
		# 	# 乘客生日
		# 	birthday, birthday_list, = self.BPR.parse_to_path(
		# 		path_syntax=f'$.dateOfBirth', source_data=i)
		# 	birthday = self.DFR.format_to_transform(birthday, "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
		# 	# 性别
		# 	gender, gender_list = self.BPR.parse_to_path(
		# 		path_syntax=f'$.gender', source_data=i)
		# 	if gender == "Female":
		# 		gender = 'F'
		# 	elif gender == "Male":
		# 		gender = 'M'
		# 	# 乘客类型
		# 	"passengerStatusType"
		# 	passenger_type, passenger_type_list = self.BPR.parse_to_path(
		# 		path_syntax=f'$.passengerStatusType', source_data=i)
		# 	if passenger_type == "Active":
		# 		passenger_type = 0
		# 	elif passenger_type == "":
		# 		passenger_type = 1
		# 	nationality, nationality_list = self.BPR.parse_to_path(
		# 		path_syntax=f'$.nationality', source_data=i)
		# 	# 证件号
		# 	number, number_temp = self.BPR.parse_to_path(
		# 		path_syntax=f'$..number', source_data=i)
		# 	# cardExpired 证件有效日期
		# 	card_expired, card_expired_temp = self.BPR.parse_to_path(
		# 		path_syntax=f'$..expirationDate', source_data=i)
		# 	aux = [
		# 		{
		# 			"departureAircode": "",
		# 			"arrivalAircode": "",
		# 			"tripType": trip_type,
		# 			"detail": detail,  # 行李
		# 			"productType": "1"  # 增值服务类型
		# 		}
		# 	]
		# 	self.passengers.append({
		# 		"passengerName": f"{last_name}/{first_name}",  # f"{last_name}/{first_name}"
		# 		"passengerBirthday": birthday,  # 乘客生日
		# 		"passengerSex": gender,         # 乘客性别
		# 		"passengerType": passenger_type,  # 乘客类型， 成人 0，  儿童 1
		# 		"passengerNationality": nationality,  # 乘客国籍
		# 		"identificationNumber": number,  # 证件号码
		# 		"cardType": "",  # 证件类型
		# 		"cardExpired": card_expired.split('T')[0],  # 证件有效日期
		# 		"service_type": "",  # 增值服务类型
		# 		"auxArray": aux  # 行李数据
		# 	})
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
