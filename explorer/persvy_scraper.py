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


class PersVYScraper(RequestWorker):
    """VY采集器，首页质检，用代理

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
        self.order_status: str = ""         # 订单状态
        self.segments: list = []            # 航段信息
        self.passengers: list = []          # 乘客信息
        self.referer_url: str = ""
    
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
        if self.CPR.username == "168033518@qq.com":
            if self.process_to_index():
                if self.process_to_login():
                    if self.process_to_segment():
                        if self.process_to_detail():
                            self.process_to_return()
                            self.logger.removeHandler(self.handler)
                            return self.callback_data
        else:
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
        # # # 解析首页
        self.RCR.url = "https://www.vueling.com/en"
        self.RCR.param_data = None
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Host": "www.vueling.com",
            "Upgrade-Insecure-Requests": "1"
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
        # # # 转换起始日期
        depart_date = self.DFR.format_to_transform(self.CPR.departure_time, "%Y-%m-%d")
        # # # 解析出发日期页面
        self.RCR.url = "https://tickets.vueling.com/LinksHub.ashx"
        self.RCR.param_data = (
            ("origin", self.CPR.departure_code), ("day", depart_date.day), ("month", depart_date.month),
            ("year", depart_date.year), ("pnr", self.CPR.record), ("event", "change"),
            ("flow", "c3"), ("culture", "en-GB"),
        )
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Host": "tickets.vueling.com",
            "Referer": "https://www.vueling.com/en",
            "Upgrade-Insecure-Requests": "1"
        })
        if self.RCR.request_to_get(status_code=302):
            # # # 解析跳转
            url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
            self.RCR.url = "https://tickets.vueling.com" + url
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Host": "tickets.vueling.com",
                "Referer": "https://www.vueling.com/en",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get(status_code=302):
                # # # 查询错误信息
                error_message, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "#validationErrorContainerReadAlongList p[role=alert]", self.RCR.page_source)
                error_message = self.BPR.parse_to_separate(error_message)
                if error_message:
                    self.logger.info(f"查询订单信息错误(*>﹏<*)【{self.CPR.record}】【{error_message}】")
                    self.callback_msg = f"查询订单信息错误(*>﹏<*)【{self.CPR.record}】【{error_message}】"
                    return False
                # # # 解析跳转
                url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                self.referer_url = "https://tickets.vueling.com" + url
                self.RCR.url = self.referer_url
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Host": "tickets.vueling.com",
                    "Referer": "https://www.vueling.com/en",
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    return True
        self.logger.info("详情超时或者错误(*>﹏<*)【detail】")
        self.callback_msg = "详情超时或者错误"
        return False

    def process_to_login(self) -> bool:
        """登录后查询航班流程
        :return:  bool
        """
        # # # 解析email页面
        self.RCR.url = "https://tickets.vueling.com/LinksHub.ashx"
        self.RCR.param_data = (
            ("email", "168033518@qq.com"), ("pnr", self.CPR.record), ("event", "change"),
            ("flow", "c3"), ("culture", "en-GB"),
        )
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Host": "tickets.vueling.com",
            "Referer": "https://www.vueling.com/en",
            "Upgrade-Insecure-Requests": "1"
        })
        if self.RCR.request_to_get(status_code=302):
            # # # 解析跳转
            url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
            self.RCR.url = "https://tickets.vueling.com" + url
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Host": "tickets.vueling.com",
                "Referer": "https://www.vueling.com/en",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get(status_code=302):
                # # # 查询错误信息
                error_message, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "#validationErrorContainerReadAlongList p[role=alert]", self.RCR.page_source)
                error_message = self.BPR.parse_to_separate(error_message)
                if error_message:
                    self.logger.info(f"查询订单信息错误(*>﹏<*)【{self.CPR.record}】【{error_message}】")
                    self.callback_msg = f"查询订单信息错误(*>﹏<*)【{self.CPR.record}】【{error_message}】"
                    return False
                # # # 解析跳转
                url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                self.referer_url = "https://tickets.vueling.com" + url
                self.RCR.url = self.referer_url
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Host": "tickets.vueling.com",
                    "Referer": "https://www.vueling.com/en",
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    return True
        self.logger.info("查询超时或者错误(*>﹏<*)【query】")
        self.callback_msg = "查询超时或者错误"
        return False

    def process_to_segment(self) -> bool:
        """收集航段信息
        :return:  bool
        """
        # # # 从详情页收集航段信息
        self.order_status, temp_list = self.DPR.parse_to_attributes(
            "value", "xpath", "//span[contains(@class, 'paymentStatus')]/text()", self.RCR.page_source)
        if not self.order_status:
            status, temp_list = self.DPR.parse_to_attributes(
                "text", "css", "div[class='paxDetailsBox__block'] div[class='paxDetailsBox__blockTitle']",
                self.RCR.page_source)
            if temp_list and "Agency contact details" in temp_list:
                self.order_status = "Confirmed"
            else:
                self.order_status = "Wrong"
        
        clock, temp_list = self.DPR.parse_to_attributes(
            "value", "xpath", "//div[@class='time_detail_flight marginTop10']/text()", self.RCR.page_source)
        flights, flights_list = self.DPR.parse_to_attributes(
            "class", "css", "div[class*=flightDetailsBox__infoFLight__block]", self.RCR.page_source)
        if flights_list:
            for i in range(1, len(flights_list)+1):
                flight_num, temp_list = self.DPR.parse_to_attributes(
                    "text", "css",
                    f"div[class*=flightDetailsBox__infoFLight__block]:nth-child({i}) "
                    f"div.flightDetailsBox__infoFLight__pnr strong", self.RCR.page_source)
                flight_num, temp_list = self.BPR.parse_to_regex(":(.*)", flight_num)
                flight_num = self.BPR.parse_to_clear(flight_num)

                flight_date, temp_list = self.DPR.parse_to_attributes(
                    "text", "css",
                    f"div[class*=flightDetailsBox__infoFLight__block]:nth-child({i}) "
                    f"p.flightDetailsBox__date span:nth-child(2)", self.RCR.page_source)
                flight_date = self.BPR.parse_to_clear(flight_date)

                flight_time, time_list = self.DPR.parse_to_attributes(
                    "text", "css",
                    f"div[class*=flightDetailsBox__infoFLight__block]:nth-child({i}) "
                    f"span.flightDetailsBox__infoFLight__time strong", self.RCR.page_source)

                stations, stations_list = self.DPR.parse_to_attributes(
                    "text", "css",
                    f"div[class*=flightDetailsBox__infoFLight__block]:nth-child({i}) "
                    f"span.flightDetailsBox__infoFLight__terminal", self.RCR.page_source)
                from_station = ""
                to_station = ""
                if len(stations_list) > 1:
                    if len(stations_list[0]) >= 3 and len(stations_list[1]) >= 3:
                        from_station = self.BPR.parse_to_clear(stations_list[0])
                        from_station = from_station[:3]
                        to_station = self.BPR.parse_to_clear(stations_list[1])
                        to_station = to_station[:3]

                from_time = ""
                to_time = ""
                if len(time_list) > 1:
                    from_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|:", "", time_list[0])
                    to_time = self.BPR.parse_to_replace("\\r|\\n|\\t|\\s|:", "", time_list[1])

                flight_date = self.DFR.format_to_transform(flight_date, "%d.%m.%Y")
                flight_date = flight_date.strftime("%Y%m%d")
                if clock:
                    to_date = self.DFR.format_to_transform(flight_date, "%Y%m%d")
                    to_date = self.DFR.format_to_custom(to_date, 1)
                    to_date = to_date.strftime("%Y%m%d")
                    arrival_time = to_date + to_time
                else:
                    arrival_time = flight_date + to_time
                departure_time = flight_date + from_time

                self.segments.append({
                    "departureAircode": from_station, "arrivalAircode": to_station,
                    "flightNum": flight_num,
                    "departureTime": departure_time, "arrivalTime": arrival_time, "tripType": i
                })

            return True

        self.logger.info("航段超时或者错误(*>﹏<*)【segments】")
        self.callback_msg = "航段超时或者错误"
        return False
    
    def process_to_detail(self) -> bool:
        """收集乘客信息
        :return:  bool
        """
        last_name, last_list = self.DPR.parse_to_attributes(
            "value", "css", "input[id*=PassengerLastName]", self.RCR.page_source)
        first_name, first_list = self.DPR.parse_to_attributes(
            "value", "css", "input[id*=PassengerFirstName]", self.RCR.page_source)
        aux = {}
        if last_list and first_list and len(last_list) == len(first_list):
            for i in range(len(last_list)):
                aux[f"{last_list[i]}/{first_list[i]}"] = []
                self.passengers.append({
                    "passengerName": f"{last_list[i]}/{first_list[i]}", "passengerBirthday": "",
                    "passengerSex": "", "passengerType": "", "passengerNationality": "",
                    "identificationNumber": "", "cardType": "", "cardExpired": "",
                    "service_type": "", "auxArray": []
                })
                
            self.RCR.url = "https://tickets.vueling.com/ChangeItinerary.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "tickets.vueling.com",
                "Origin": "https://tickets.vueling.com",
                "Referer": self.referer_url,
                "Upgrade-Insecure-Requests": "1"
            })
            # # # 拼接参数，解析退出
            param_batch = [
                ("__EVENTTARGET", False, "BaggageButton"),
                ("__EVENTARGUMENT", True, "#eventArgument"),
                ("__VIEWSTATE", True, "#viewState"),
                ("pageToken", True, "input[name='pageToken']"),
                ("TravelDocsMustBlockForm", False, "false"),
                ("pnr", False, ""),
                ("PnrHasTravelDocumentData", False, "false"),
                ("PnrHasTravelDocumentData", False, "false"),
                ("SmartMailChangeItineraryView$Prefix", False, ""),
                ("SmartMailChangeItineraryView$Phone", False, "")
            ]
            for i in range(len(last_list)):
                param_batch.extend([
                    ("PassengerEmail[]", False, ""),
                    ("PassengerPhonePrefix[]", False, ""),
                    ("PassengerPhoneNumber[]", False, ""),
                    ("PassengerNumber[]", False, i),
                    ("PassengerFirstName[]", False, first_list[i]),
                    ("PassengerLastName[]", False, last_list[i])
                ])
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.page_source)
            if self.RCR.request_to_post(status_code=302):
                self.RCR.url = "https://tickets.vueling.com/ChangeBaggage.aspx"
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Host": "tickets.vueling.com",
                    "Referer": self.referer_url,
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    booking_data, temp_list = self.BPR.parse_to_regex('"CurrentBooking":.*"OldBooking":', self.RCR.page_source)
                    booking_data, temp_list = self.BPR.parse_to_regex('{.*}', booking_data)
                    booking_data = self.BPR.parse_to_dict(booking_data)
                    journey, journey_list = self.BPR.parse_to_path(f"$.Journey..Passenger", booking_data)
                    if journey_list:
                        for n, v in enumerate(journey_list):
                            for i, k in enumerate(v):
                                baggage, baggage_list = self.BPR.parse_to_path("$.SSRS..Code", k)
                                if baggage_list:
                                    bg = 0
                                    for b in baggage_list:
                                        b_int, temp_list = self.BPR.parse_to_regex("\d+", b)
                                        b_int = self.BFR.format_to_int(b_int)
                                        bg += b_int
                                    if bg:
                                        aux[f"{last_list[i]}/{first_list[i]}"].append(
                                            {'departureAircode': '', 'arrivalAircode': '', 'tripType': n+1,
                                             'detail': f"{bg}KG", 'productType': '1'})
                    
                    for p in self.passengers:
                        for a, v in aux.items():
                            if a == p['passengerName']:
                                p['auxArray'] = v
                    return True

        self.logger.info("乘客超时或者错误(*>﹏<*)【passengers】")
        self.callback_msg = "乘客超时或者错误"
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

