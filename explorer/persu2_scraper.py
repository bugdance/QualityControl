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


class PersU2Scraper(RequestWorker):
    """U2采集器，首页质检, 用代理

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
        self.RCR.url = "https://www.easyjet.com/en/?lang=EN"
        self.RCR.param_data = None
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Host": "www.easyjet.com",
            "Upgrade-Insecure-Requests": "1"
        })
        if self.RCR.request_to_get():
            # # # 解析首页查询pnr
            self.RCR.url = "https://www.easyjet.com/ejrebooking/api/v31/account/passengerlogin"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "Host": "www.easyjet.com",
                "Origin": "https://www.easyjet.com",
                "Referer": "https://www.easyjet.com/en/?lang=EN",
                "ADRUM": "isAjax:true",
                "x-b2b-misc": "",
                "X-Requested-With": "XMLHttpRequest",
                "X-Transaction-Id": "",
            })
            self.RCR.post_data = {"Surname": self.CPR.last_name, "BookingReference": self.CPR.record, "Persist": False}
            if self.RCR.request_to_post("json"):
                if not self.RCR.page_source:
                    self.logger.info(f"查询不到订单信息(*>﹏<*)【{self.CPR.record}】")
                    self.callback_msg = f"查询不到订单信息(*>﹏<*)【{self.CPR.record}】"
                    return False
                # # # 解析跳转
                self.RCR.url = f"https://www.easyjet.com/EN/BoardingPass/ViewBoardingPassList/{self.CPR.record}/{self.CPR.last_name}"
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Host": "www.easyjet.com",
                    "Referer": "https://www.easyjet.com/en/?lang=EN",
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get(status_code=302):
                    # # # 解析跳转
                    url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                    self.RCR.url = "https://www.easyjet.com" + url
                    self.RCR.param_data = None
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Host": "www.easyjet.com",
                        "Referer": "https://www.easyjet.com/en/?lang=EN",
                        "Upgrade-Insecure-Requests": "1"
                    })
                    if self.RCR.request_to_get(status_code=302):
                        if self.RCR.page_source:
                            return True
                        
        self.logger.info("首页超时或者错误(*>﹏<*)【home】")
        self.callback_msg = "首页超时或者错误"
        return False
    
    def process_to_search(self) -> bool:
        """查询详情信息流程
        :return:  bool
        """
        # # # 解析详细页面跳转
        referer_url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
        self.RCR.url = "https://www.easyjet.com" + referer_url
        self.RCR.param_data = None
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Host": "www.easyjet.com",
            "Referer": "https://www.easyjet.com/en/?lang=EN",
            "Upgrade-Insecure-Requests": "1"
        })
        if self.RCR.request_to_get():
            # # # 解析下一页参数
            wa, temp_list = self.DPR.parse_to_attributes("value", "css", "input[name=wa]", self.RCR.page_source)
            w_result, temp_list = self.DPR.parse_to_attributes("value", "css", "input[name=wresult]", self.RCR.page_source)
            w_ctx, temp_list = self.DPR.parse_to_attributes("value", "css", "input[name=wctx]", self.RCR.page_source)
            # # # 解析跳转
            self.RCR.url = "https://www.easyjet.com/en/secure/Federation.mvc/FederatedSignIn"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "www.easyjet.com",
                "Origin": "https://www.easyjet.com",
                "Referer": "https://www.easyjet.com" + referer_url,
                "Upgrade-Insecure-Requests": "1"
            })
            self.RCR.post_data = [
                ("wa", wa), ("wresult", w_result), ("wctx", w_ctx),
            ]
            if self.RCR.request_to_post(status_code=302):
                # # # 解析详细页面
                url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                self.RCR.url = "https://www.easyjet.com" + url
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Host": "www.easyjet.com",
                    "Referer": "https://www.easyjet.com" + referer_url,
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    # # # 查询订单状态
                    disrupted_head, temp_list = self.DPR.parse_to_attributes(
                        "class", "css", ".ViewBookingApisDisruptedHead", self.RCR.page_source)
                    apis_link, temp_list = self.DPR.parse_to_attributes("id", "css", "#apisLink", self.RCR.page_source)
                    if disrupted_head or apis_link:
                        self.logger.info("查询订单状态异常(*>﹏<*)【detail】")
                        self.callback_msg = "查询订单状态异常"
                        return False

                    self.order_status = "Confirmed"
                    return True
        
        self.logger.info("详情超时或者错误(*>﹏<*)【detail】")
        self.callback_msg = "详情超时或者错误"
        return False
    
    def process_to_segment(self) -> bool:
        """收集航段信息
        :return:  bool
        """
        flight_num, num_list = self.DPR.parse_to_attributes(
            "text", "css",
            "div.viewBookingSectionContentDetailFlightInfo>div.row:nth-child(2)>p:nth-child(1)>strong",
            self.RCR.page_source)
        flight_date, date_list = self.DPR.parse_to_attributes(
            "value", "xpath", "//p[@class='viewBookingSectionContentDetailFlightDate']/text()[2]", self.RCR.page_source)
        from_time, from_list = self.DPR.parse_to_attributes(
            "text", "css", "div.viewBookingSectionContentDetailFlight div.departure span.normal", self.RCR.page_source)
        to_time, to_list = self.DPR.parse_to_attributes(
            "text", "css", "div.viewBookingSectionContentDetailFlight div.arrival span.normal", self.RCR.page_source)
        
        if num_list:
            for i in range(len(num_list)):
                flight_num, temp_list = self.BPR.parse_to_regex("\d+", num_list[i])
                flight_num = "U2" + flight_num
                
                from_time = self.BPR.parse_to_replace(":", "", from_list[i])
                to_time = self.BPR.parse_to_replace(":", "", to_list[i])
                
                flight_date = self.BPR.parse_to_clear(date_list[i])
                flight_date = self.DFR.format_to_transform(flight_date, '%A,%d%B%Y')
                flight_date = flight_date.strftime("%Y%m%d")
                if int(from_time) > int(to_time):
                    to_date = self.DFR.format_to_transform(flight_date, "%Y%m%d")
                    to_date = self.DFR.format_to_custom(to_date, 1)
                    to_date = to_date.strftime("%Y%m%d")
                    arrival_time = to_date + to_time
                else:
                    arrival_time = flight_date + to_time
                departure_time = flight_date + from_time
                
                self.segments.append({
                    "departureAircode": "", "arrivalAircode": "", "flightNum": flight_num,
                    "departureTime": departure_time, "arrivalTime": arrival_time, "tripType": i+1
                })
                
            return True
            
        self.logger.info("航段超时或者错误(*>﹏<*)【segments】")
        self.callback_msg = "航段超时或者错误"
        return False
    
    def process_to_detail(self) -> bool:
        """收集乘客信息
        :return:  bool
        """
        baggage, temp_list = self.DPR.parse_to_attributes("text", "css", "p.normalFont>strong", self.RCR.page_source)
        baggage_total, temp_list = self.BPR.parse_to_regex("\d+", baggage)
        aux = []
        if baggage_total:
            aux = [
                {'departureAircode': '', 'arrivalAircode': '', 'tripType': 1, 'detail': f"{baggage_total}KG", 'productType': '1'},
                {'departureAircode': '', 'arrivalAircode': '', 'tripType': 2, 'detail': f"{baggage_total}KG", 'productType': '1'}
            ]
            
        full_name, temp_list = self.DPR.parse_to_attributes(
            "text", "css", "p.travellersName>strong", self.RCR.page_source)
        full_name = self.BPR.parse_to_separate(full_name)
        full_name = full_name.split(", ")
        if full_name:
            for i in full_name:
                if len(i) > 1:
                    sex = ""
                    if "(child)" not in i:
                        age_type = 0
                        name = i.split(" ")
                        last_name = name[-1]
                        first_name = ""
                        if "Mr" in name[0]:
                            if "Mrs" in name[0]:
                                sex = "F"
                            else:
                                sex = "M"
                        else:
                            sex = "F"
                        for j in range(1, len(name) - 1):
                            first_name += name[j]
                    else:
                        age_type = 1
                        name = i.split(" ")
                        name.pop(-1)
                        last_name = name[-1]
                        first_name = ""
                        for j in range(len(name) - 1):
                            first_name += name[j]
                
                    self.passengers.append({
                        "passengerName": f"{last_name}/{first_name}", "passengerBirthday": "",
                        "passengerSex": sex, "passengerType": age_type, "passengerNationality": "",
                        "identificationNumber": "", "cardType": "", "cardExpired": "",
                        "service_type": "", "auxArray": aux
                    })
            
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

