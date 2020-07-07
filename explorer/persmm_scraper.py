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
from collector.persmm_mirror import PersMMMirror


class PersMMScraper(RequestWorker):
    """MM采集器，MM网站流程交互，5分钟刷abck，10分钟封禁解禁。"""
    
    def __init__(self) -> None:
        RequestWorker.__init__(self)
        self.RCR = RequestCrawler()  # 请求爬行器。
        self.AFR = AESFormatter()  # AES格式器。
        self.BFR = BasicFormatter()  # 基础格式器。
        self.BPR = BasicParser()  # 基础解析器。
        self.CFR = CallBackFormatter()  # 回调格式器。
        self.CPR = CallInParser(False)  # 接入解析器。
        self.DFR = DateFormatter()  # 日期格式器。
        self.DPR = DomParser()  # 文档解析器。
        self.PMR = PersMMMirror()  # MM镜像器。
        # # # 请求中用到的变量
        self.verify_token: str = ""     # 认证token
        # # # 返回中用到的变量
        self.order_status: str = ""     # 订单状态
        self.segments: list = []        # 航段信息
        self.passengers: list = []      # 乘客信息
    
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
        self.PMR.logger = self.logger
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
        # self.process_to_proxy()
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

    def process_to_proxy(self, count: int = 0, max_count: int = 3) -> bool:
        """Proxy process. 代理过程。

		Args:
			count (int): 累计计数。
			max_count (int): 最大计数。

		Returns:
			bool
		"""
        if count >= max_count:
            return False
        else:
            # # # 获取代理，并配置代理。
            self.RCR.url = 'http://cloudmonitorproxy.51kongtie.com/Proxy/getProxyByServiceType?proxyNum=1&serviceType=4'
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.param_data = None
            if self.RCR.request_to_get('json'):
                ip, temp_list = self.BPR.parse_to_path("$.[0].proxyIP", self.RCR.page_source)
                port, temp_list = self.BPR.parse_to_path("$.[0].prot", self.RCR.page_source)
                if ip and port:
                    proxy = f"http://yunku:123@{ip}:{port}"
                    self.RCR.set_to_proxy(True, proxy)
                    return True
            # # # 错误重试。
            self.logger.info(f"请求代理第{count + 1}次超时(*>﹏<*)【proxy】")
            self.callback_msg = f"请求代理第{count + 1}次超时，请重试。"
            return self.process_to_proxy(count + 1, max_count)
    
    def process_to_index(self) -> bool:
        """首页查询航班流程
        :return:  bool
        """
        # # # 请求接口服务。
        self.RCR.url = "http://45.81.129.1:33334/produce/mm/"
        self.RCR.param_data = None
        self.RCR.header = None
        self.RCR.post_data = {"mm": "abck"}
        if not self.RCR.request_to_post("json", "json"):
            self.logger.info(f"请求刷值地址失败(*>﹏<*)【45.81.129.1:33334】")
            self.callback_msg = "请求刷值地址失败，请通知技术检查程序。"
            return False
        # # # 获取abck。
        cookie = self.RCR.page_source.get("value")
        if not cookie:
            self.logger.info(f"刷值数量不够用(*>﹏<*)【45.81.129.1:33334】")
            self.callback_msg = "刷值数量不够用，请通知技术检查程序。"
            return False
        # # # 设置cookie。
        cookies = [
            {"domain": "ezy.flypeach.com", "name": "_abck", "path": "/", "value": cookie},
        ]
        self.RCR.set_to_cookies(True, cookies)
        
        # # # 爬取首页
        self.RCR.url = "https://ezy.flypeach.com/cn/manage/manage-authenitcate"
        self.RCR.param_data = None
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Host": "ezy.flypeach.com",
            "Upgrade-Insecure-Requests": "1"
        })
        if self.RCR.request_to_get():
            # # # 解析查询页获取token
            self.verify_token, temp_list = self.DPR.parse_to_attributes(
                "value", "css", "#form0 [name=__RequestVerificationToken]", self.RCR.page_source)
            if self.verify_token:
                return True
        self.logger.info("首页超时或者错误(*>﹏<*)【home】")
        self.callback_msg = "首页超时或者错误"
        return False

    def process_to_search(self) -> bool:
        """查询详情信息流程
        :return:  bool
        """
        # # # 从查询页爬取详情页
        self.RCR.url = "https://ezy.flypeach.com/cn/manage/manage-authenitcate"
        self.RCR.param_data = None
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": "ezy.flypeach.com",
            "Origin": "https://ezy.flypeach.com",
            "Referer": "https://ezy.flypeach.com/cn/manage/manage-authenitcate",
            "Upgrade-Insecure-Requests": "1"
        })
        self.RCR.post_data = [
            ("__RequestVerificationToken", self.verify_token), ("PNR", self.CPR.record),
            ("lastName", self.CPR.last_name),
        ]
        if self.RCR.request_to_post(status_code=302):
            # # # 解析详情页获取error
            error_message, temp_list = self.DPR.parse_to_attributes(
                "text", "css", "div.login-error", self.RCR.page_source)
            error_message = self.BPR.parse_to_separate(error_message)
            if error_message:
                self.logger.info(f"查询订单信息错误(*>﹏<*)【{self.CPR.record}】【{error_message}】")
                self.callback_msg = error_message
                return False
            # # # 解析跳转
            url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
            self.RCR.url = "https://ezy.flypeach.com" + url
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Host": "ezy.flypeach.com",
                "Referer": "https://ezy.flypeach.com/cn/manage/manage-authenitcate",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                change, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "button[data-target='#scheduleChange']", self.RCR.page_source)
                change = self.BPR.parse_to_clear(change)
                if change:
                    self.logger.info(f"详情超时或者错误(*>﹏<*)【{change}】")
                    self.callback_msg = change
                    return False
                status, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", ".remaining-date", self.RCR.page_source)
                status = self.BPR.parse_to_clear(status)
                if "取消" in status:
                    self.logger.info(f"详情超时或者错误(*>﹏<*)【{status}】")
                    self.callback_msg = status
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
        # # # 从详情页收集航段信息
        segments, temp_list = self.BPR.parse_to_regex('segments: \[{"Id".*?null}]', self.RCR.page_source)
        segments, temp_list = self.BPR.parse_to_regex("\[{.*null}]", segments)
        segments_list = self.BPR.parse_to_list(segments)
        if segments_list:
            # # # 循环航段提取数据
            for n, i in enumerate(segments_list):
                legs, temp_list = self.BPR.parse_to_path("$.Legs[0]", i)
                if legs:
                    from_date = legs.get('DepartureDateString')
                    from_date = self.DFR.format_to_transform(from_date, "%Y-%m-%d")
                    from_date = from_date.strftime("%Y%m%d")
                    from_time = legs.get('DepartureTimeString')
                    from_time = self.DFR.format_to_transform(from_time, "%H:%M:%S")
                    from_time = from_time.strftime("%H%M")

                    to_date = legs.get('ArrivalDateString')
                    to_date = self.DFR.format_to_transform(to_date, "%Y-%m-%d")
                    to_date = to_date.strftime("%Y%m%d")
                    to_time = legs.get('ArrivalTimeString')
                    to_time = self.DFR.format_to_transform(to_time, "%H:%M:%S")
                    to_time = to_time.strftime("%H%M")

                    departure_code, temp_list = self.BPR.parse_to_path("$.Origin.Code", legs)
                    arrival_code, temp_list = self.BPR.parse_to_path("$.Destination.Code", legs)
                    flight_code, temp_list = self.BPR.parse_to_path("$.Carrier.Code", legs)
                    flight_code = self.BPR.parse_to_clear(flight_code)
                    flight_digital, temp_list = self.BPR.parse_to_path("$.FlightNumber", legs)
                    flight_digital = self.BPR.parse_to_clear(flight_digital)

                    self.segments.append({
                        "departureAircode": departure_code, "arrivalAircode": arrival_code,
                        "flightNum": flight_code + flight_digital, "departureTime": from_date + from_time,
                        "arrivalTime": to_date + to_time, "tripType": n+1
                    })
            return True
        self.logger.info("航段超时或者错误(*>﹏<*)【segments】")
        self.callback_msg = "航段超时或者错误"
        return False

    def process_to_detail(self) -> bool:
        """收集乘客信息
        :return:  bool
        """
        person_id, person_list = self.DPR.parse_to_attributes(
            "id", "css", "div[class*='extraDetail'][style*='block'] div.extra-person.extraPerson", self.RCR.page_source)
        person_aux = {}
        for i in person_list:
            name, name_list = self.DPR.parse_to_attributes(
                "text", "css", f"div[class*='extraDetail'][style*='block'] div[id={i}] label[class*='ssr_passenger_']",
                self.RCR.page_source)
            name = self.BPR.parse_to_separate(name)
            name = name.replace(" ", "/")

            person_list = []
            num, num_list = self.DPR.parse_to_attributes(
                "text", "css", f"div[class*='extraDetail'][style*='block'] div[id={i}] "
                f"select[id^='dd'][id$='_0'] option[value='INCLUDED']",
                self.RCR.page_source)
            if num_list:
                for n, j in enumerate(num_list):
                    single_dict = {"departureAircode": "", "arrivalAircode": "", "tripType": 1, "detail": "", "productType": "1"}
                    j = self.BPR.parse_to_clear(j)
                    count, temp_list = self.BPR.parse_to_regex("(.*)件", j)
                    count, temp_list = self.BPR.parse_to_regex("\d+", count)
                    if count:
                        count = self.BFR.format_to_int(count)
                        bg = f"{count * 20}KG"
                        single_dict['tripType'] = n + 1
                        single_dict['detail'] = bg
                        person_list.append(single_dict)
            else:
                num, num_list = self.DPR.parse_to_attributes(
                    "text", "css", f"div[class*='extraDetail'][style*='block'] div[id={i}] "
                    f"select[id^='multipleOfSsr'][id$='_0'] option[data-is-default-selected='true']",
                    self.RCR.page_source)
                if num_list:
                    for n, j in enumerate(num_list):
                        single_dict = {"departureAircode": "", "arrivalAircode": "", "tripType": 1, "detail": "", "productType": "1"}
                        j = self.BPR.parse_to_clear(j)
                        j = j.replace("+", "")
                        j = self.BFR.format_to_int(j)
                        bg = f"{j*20}KG"
                        single_dict['tripType'] = n+1
                        single_dict['detail'] = bg
                        person_list.append(single_dict)
            person_aux[name] = person_list
            
        # # # 从详情页收集乘客信息，先判断是否有护照
        pass_port, temp_list = self.DPR.parse_to_attributes(
            "name", "css", "input[name=passengerPassportExpiryDate]", self.RCR.page_source)
            
        passengers, temp_list = self.BPR.parse_to_regex("var passengers = JSON.parse\('.*?'\)", self.RCR.page_source)
        passengers, temp_list = self.BPR.parse_to_regex("\[{.*}\]", passengers)
        passengers = self.BPR.parse_to_replace('\\\\"', '"', passengers)
        passengers_list = self.BPR.parse_to_list(passengers)
        if passengers_list:
            # # # 循环乘客提取数据
            for i in passengers_list:
                age_type = 0
                age_name = self.BPR.parse_to_path("$.PassengerType.Name", i)
                if "成人" in age_name:
                    age_type = 0
                elif "儿童" in age_name:
                    age_type = 1
                elif "婴儿" in age_name:
                    age_type = 2
                # # # 判断是否有护照
                card_expire = ""
                if pass_port:
                    expire_date, temp_list = self.BPR.parse_to_path("$.PassPortExpireDate", i)
                    card_expire = self.DFR.format_to_timestamp(expire_date)
                    card_expire = card_expire.strftime("%Y-%m-%d")
                # # # 判断是否需要解析国籍
                nationality, temp_list = self.BPR.parse_to_path("$.Nationality", i)
                nationality = self.BPR.parse_to_clear(nationality)
                if nationality:
                    nationality_code, temp_list = self.BPR.parse_to_regex("\d+", nationality)
                    if nationality_code:
                        nationality_code = self.BFR.format_to_int(nationality_code)
                        nationality = self.PMR.select_from_nationality(nationality_code)
                # # # 其他数据
                last_name, temp_list = self.BPR.parse_to_path("$.LastName", i)
                first_name, temp_list = self.BPR.parse_to_path("$.FirstName", i)
                sex, temp_list = self.BPR.parse_to_path("$.Gender", i)
                card_num, temp_list = self.BPR.parse_to_path("$.PassPortNumber", i)
                
                birthday, temp_list = self.BPR.parse_to_path("$.BirthDate", i)
                birthday = self.DFR.format_to_timestamp(birthday)
                birthday = birthday.strftime("%Y-%m-%d")
                
                aux_array = []
                for k, v in person_aux.items():
                    if k == f"{last_name}/{first_name}":
                        aux_array = v
                        
                self.passengers.append({
                    "passengerName": f"{last_name}/{first_name}", "passengerBirthday": birthday,
                    "passengerSex": sex, "passengerType": age_type, "passengerNationality": nationality,
                    "identificationNumber": card_num, "cardType": "", "cardExpired": card_expire,
                    "service_type": "", "auxArray": aux_array
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

