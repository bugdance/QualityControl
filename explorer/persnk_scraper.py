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


class PersNKScraper(RequestWorker):
    """生日差一天"""

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
        
        if self.get_authorization():
            if self.get_data():
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

    def get_authorization(self):

        self.RCR.url = 'https://api.spirit.com/dotrez2/api/nsk/v1/token'
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            'Pragma': 'no-cache',
            'Origin': 'https://www.spirit.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Sec-Fetch-Mode': 'cors',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache',
            'Referer': 'https://www.spirit.com/',
            'Ocp-Apim-Subscription-Key': 'd915d5442ee6427bb58e33dd93e253b8',
        })

        self.RCR.post_data = '{"applicationName":"dotRezWeb"}'
        if self.RCR.request_to_post(is_redirect=True,status_code=201):
            authorization = self.BPR.parse_to_path('$..token',self.BPR.parse_to_dict(self.RCR.page_source))[0]
            self.authorization = 'Bearer ' + authorization
            return True
        self.logger.info("获取authorization失败(*>﹏<*)")
        self.callback_msg = "authorization失败"
        return False

    def get_data(self):

        self.RCR.url = 'https://api.spirit.com/dotrez2/api/nsk/nk/booking/retrieve'
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            'Pragma': 'no-cache',
            'Origin': 'https://www.spirit.com',
            'Accept-Language': 'en-US',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Ocp-Apim-Subscription-Key': 'd915d5442ee6427bb58e33dd93e253b8',
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/plain, */*',
            'Cache-Control': 'no-cache',
            'Authorization': self.authorization,
            'Referer': 'https://www.spirit.com/',
            'Sec-Fetch-Mode': 'cors',
        })
        self.RCR.param_data = (
            ('lastName', self.CPR.last_name),
            ('recordLocator', self.CPR.record),
        )
        if self.RCR.request_to_get():
            if 'errors' in self.RCR.page_source:
                self.logger.info("姓名或票号错误(*>﹏<*)")
                self.callback_msg = "传入参数错误"
                return False
            self.data = self.RCR.page_source
            self.data = self.BPR.parse_to_dict(self.RCR.page_source)

            isCancelled, temp_list = self.BPR.parse_to_path('$..isCancelled',self.data)
            if isCancelled:
                self.logger.info("行程已被取消")
                self.callback_msg = "行程已被取消"
                return False
            
            if 'Carry-On' in self.RCR.page_source:
                self.logger.info("有手提行李(*>﹏<*)【passengers】")
                self.callback_msg = "发现额外手提行李，需要人工核实"
                return False
            return True

    def process_to_detail(self) -> bool:

        self.status = self.BPR.parse_to_path('$..info.status',self.data)[0]
        dict = {
            0: "Default",
            1: "Hold",
            2: "Confirmed",
            3: "Closed",
            4: "Hold Canceled",
            5: "Pending Archive",
            6: "Archived"
        }
        for m,n in dict.items():
            if self.status == m:
                self.order_status = n

        passenger_list = self.BPR.parse_to_path('$..passengers',self.data)[0]
        if passenger_list:
            for passenger in passenger_list.values():
                auxArray = []
                for key,value in passenger.items():
                    if key =="fees":
                        tType = 1
                        # print(json.dumps(value))
                        dt = ""
                        luggage = {}
                        for m in value:

                            if  m['type'] == 6 :
                                a = 1
                                detail = str(m['ssrNumber'] * 18)+'kg'
                                d_code = m['flightReference'][-6:-3]
                                a_code = m['flightReference'][-3:]
                                if d_code == dt:
                                    luggage['detail'] = str(int(luggage['detail'][0:2])+18) + 'kg'
                                    break
                                luggage = {
                                    "departureAircode": d_code,
                                    "arrivalAircode": a_code,
                                    "tripType": tType,
                                    "detail": detail,
                                    "productType": "1"
                                }
                                auxArray.append(luggage)
                                a += 1
                                tType += 1
                                dt = d_code
                                if a > 2:
                                    break
               
                # 性别
                birthday = self.BPR.parse_to_path('$.info.dateOfBirth',passenger)[0][:10]
                
                if self.BPR.parse_to_path('$..gender',passenger)[0] == 1:
                    gender = 'M'
                else:
                    gender = "F"
                passenger_type, temp_list = self.BPR.parse_to_path('$.passengerTypeCode',passenger)
                if passenger_type == 'ADT':
                    age_type = 0
                elif passenger_type == 'CHD':
                    age_type = 1
                else:
                    age_type = 99
                
                last_name = self.BPR.parse_to_path('$..last',passenger)[0]
                first_name = self.BPR.parse_to_path('$..first',passenger)[0]

                self.passengers.append({
                    "passengerName": f"{last_name}/{first_name}", "passengerBirthday": birthday,
                    "passengerSex": gender, "passengerType": age_type, "passengerNationality": "",
                    "identificationNumber": "", "cardType": "", "cardExpired": "",
                    "service_type": "","auxArray":auxArray
                })
            return True
        self.logger.info("乘客超时或者错误(*>﹏<*)【passengers】")
        self.callback_msg = "乘客超时或者错误"

        return False

    def process_to_segment(self) -> bool:

        semgents = self.BPR.parse_to_path('$..journeys',self.data)[0]
        tripType = 1
        if semgents:
            for semgent in semgents:
                arr_code = self.BPR.parse_to_path('$..segments..designator.destination',semgent)[0]
                dep_code = self.BPR.parse_to_path('$..segments..designator.origin',semgent)[0]
                flight_number = self.BPR.parse_to_path('$..identifier.carrierCode',semgent)[0]+ self.BPR.parse_to_path('$..identifier.identifier',semgent)[0]
                dep_time = self.BPR.parse_to_path('$.designator.departure',semgent)[0]
                dep_time = self.BPR.parse_to_replace('-|T|:','',dep_time)[:-2]
                arr_time = self.BPR.parse_to_path('$.designator.arrival',semgent)[0]
                arr_time = self.BPR.parse_to_replace('-|T|:','',arr_time)[:-2]

                self.segments.append({
                    "arrivalAircode": arr_code,
                    "arrivalTime": arr_time,
                    "departureAircode": dep_code,
                    "departureTime": dep_time,
                    "flightNum": flight_number,
                    "tripType": tripType
                })
                tripType += 1
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




