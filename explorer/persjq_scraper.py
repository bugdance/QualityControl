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
import json



class PersJQScraper(RequestWorker):

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
        self.verify_token: str = ""     # 认证token
        # # # 返回中用到的变量
        self.order_status: str = ""     # 订单状态
        self.segments: list = []        # 航段信息
        self.passengers: list = []      # 乘客信息
        self.auxArray: list = []        # 辅营信息

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


    def process_to_detail(self):

        self.RCR.url = 'https://booking.jetstar.com/api/v1/mmb/booking/RetrieveBooking'
        self.RCR.param_data = (
            ('pnr', self.CPR.record),
            ('identifier', self.CPR.last_name),
            ('RequireInitializeSession', 'true'),
            ('isRefreshSession', 'true'),
        )
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            'sec-fetch-mode': 'cors',
            'authority': 'booking.jetstar.com',
            'referer': 'https://booking.jetstar.com/mmb/',
        })
        if self.RCR.request_to_get():
            self.order_status = self.BPR.parse_to_path('$..bookingStatus',json.loads(self.RCR.page_source))[0]
            if not self.order_status:
                self.callback_data['msg'] = '加载页面错误'
                self.logger.info('加载页面错误')
                return False
            if self.BPR.parse_to_path('$..bookingStatus',json.loads(self.RCR.page_source))[0] == 'Hold':
                self.callback_msg = "订单未支付，重点关注"
                self.logger.info('订单未支付 ')
                return False
            segments_list = self.BPR.parse_to_path('$..journeysData',json.loads(self.RCR.page_source))[0]
            count = 1
            for segment in segments_list:
                self.dep_code = self.BPR.parse_to_path('$..departStationCode',segment)[0]
                self.arr_code = self.BPR.parse_to_path('$..arrivalStationCode',segment)[0]
                dep_city = self.BPR.parse_to_path('$..departStation',segment)[0]
                arr_city = self.BPR.parse_to_path('$..arrivalStation',segment)[0]
                self.city_dict = {
                    dep_city:self.dep_code,
                    arr_city:self.arr_code
                }
                flight_num = self.BPR.parse_to_path('$.flightNumber',segment)[0].replace(' ','')
                from_date = self.BPR.parse_to_replace('-|:| ','',self.BPR.parse_to_path('$.departTime',segment)[0])[:-2]
                to_date = self.BPR.parse_to_replace('-|:| ','',self.BPR.parse_to_path('$.arrivalTime',segment)[0])[:-2]
                trip_type = count
                self.segments.append({
                    "departureAircode": self.dep_code, "arrivalAircode": self.arr_code,
                    "flightNum": flight_num, "departureTime": from_date,
                    "arrivalTime": to_date, "tripType": trip_type
                })

            passengers_list = self.BPR.parse_to_path('$..passengers', json.loads(self.RCR.page_source))[0]
            for passenger in passengers_list:
                last_name = self.BPR.parse_to_path('$..lastName',passenger)[0]
                first_name = self.BPR.parse_to_path('$..firstName',passenger)[0]
                gender = self.BPR.parse_to_path('$..gender',passenger)[0]
                if gender == 'Male':
                    gender = "M"
                else:
                    gender = "F"
                age_type = self.BPR.parse_to_path('$..passengerType',passenger)[0]

                if age_type == "ADT":
                    age_type = 0
                else:
                    age_type = 1
                auxArray = self.BPR.parse_to_path('$..passengerType',passenger)[0]
                self.passengers.append({
                    "passengerName": f"{last_name}/{first_name}", "passengerBirthday": '',
                    "passengerSex": gender, "passengerType": age_type, "passengerNationality": "",
                    "identificationNumber": "", "cardType": "", "cardExpired": "",
                    "service_type": "", "auxArray": []
                })
            return True

    def process_to_segment(self):
        self.RCR.url = 'https://booking.jetstar.com/api/v1/mmb/booking/InclusionProduct'
        if self.RCR.request_to_get():
            products_list = self.BPR.parse_to_path('$..products',json.loads(self.RCR.page_source))[0]
            for product in products_list:
                if product['productName'] == 'CheckedBaggage':
                    for luggage_data in product['journeyItems']:
                        departureAircode = luggage_data['departStation']
                        arrivalAircode = luggage_data['arrivalStation']
                        passengerNumber = luggage_data['passengerNumber']
                        try:
                            detail = luggage_data['productInfos'][0]['productDesc']
                        except:
                            detail = ''

                        if self.city_dict[departureAircode] == self.dep_code:
                            tripType = 1
                        else :
                            tripType = 2
                        luggage_data = {
                                "departureAircode": self.city_dict[departureAircode],
                                "arrivalAircode": self.city_dict[arrivalAircode],
                                "tripType": tripType,
                                "detail": detail,
                                "productType": "1"
                            }
                        if detail != '':
                            self.passengers[passengerNumber]['auxArray'].append(luggage_data)


            return True

    def return_to_data(self) -> bool:
        """返回结果数据
        :return:  bool
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
