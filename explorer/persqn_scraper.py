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
from lxml import etree


class PersQNScraper(RequestWorker):
    """QN采集器

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
        
        if self.query_from_home():
            if self.parse_captcha():
                if self.post_captcha():
                    if self.get_details():
                        self.process_to_return()
                        self.logger.removeHandler(self.handler)
                        return self.callback_data
        # # # 错误返回。
        self.callback_data['msg'] = self.callback_msg
        # self.callback_data['msg'] = "解决问题中，请人工质检。"
        self.logger.info(self.callback_data)
        self.logger.removeHandler(self.handler)
        return self.callback_data

    def query_from_home(self) -> bool:
        """
        
        Returns:

        """
        self.RCR.url = 'http://user.qunar.com/order/query.jsp?ret=http://user.qunar.com/flight_toolbox.jsp?catalog=ownorders&from=myorder&jump=0'
        self.RCR.headers = {
            'Proxy-Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Referer': 'http://flight.order.qunar.com/flight/findbyorder.html?ordertoken=ecfddf8d371e4cd0a2255d8e0d373c6e',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        if self.RCR.request_to_get():
            self.link = self.DPR.parse_to_attributes('text','xpath','//*[@id="vcodeImg_v1"]/@src',
                                                    self.RCR.page_source)[0]
            return True

    def parse_captcha(self):
        """
        
        Returns:

        """
        self.RCR.url = self.link
        if self.RCR.request_to_get(page_type='content'):
            self.RCR.url = 'http://119.3.234.171:33333/captcha/qn/'
            self.RCR.post_data = {
                'img': self.RCR.page_source

            }
            if self.RCR.request_to_post(data_type='files'):

                self.captcha = self.BPR.parse_to_dict(self.RCR.page_source).get('result')
                return True

    def post_captcha(self):
        """
        
        Returns:

        """
        self.RCR.url = 'https://user.qunar.com/order/queryResult.jsp'
        self.RCR.headers = {
            'sec-fetch-mode': 'cors',
            'origin': 'https://user.qunar.com',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'x-requested-with': 'XMLHttpRequest',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'accept': '*/*',
            'referer': 'https://user.qunar.com/order/query.jsp?ret=http%3A%2F%2Fuser.qunar.com%2Fflight_toolbox.jsp%3Fcatalog%3Downorders%26from%3Dmyorder&jump=0',
            'authority': 'user.qunar.com',
            'sec-fetch-site': 'same-origin',
        }
        self.RCR.post_data = {
            'orderno': self.CPR.record,
            'prenum': '86',
            'mobile': '16639167479',
            'orderType': '1',
            'querytype': '3',
            'vcode': self.captcha
        }

        if self.RCR.request_to_post():
            self.page_url = self.BPR.parse_to_dict(self.RCR.page_source).get("redirect")
            self.ordertoken = self.BPR.parse_to_regex('http://flight.order.qunar.com/flight/findbyorder.html\?ordertoken=(.{32})',self.page_url)[0]
            self.RCR.url = f'https://order.flight.qunar.com/nts/order/pay/orderNo_{self.CPR.record}_otaType_5_biz_interNTS_bizType_1'
            self.RCR.post_data = {
                'ordertoken': self.ordertoken
            }
            self.RCR.headers = {
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Origin': 'https://order.flight.qunar.com',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
                'Sec-Fetch-Site': 'none',
                'Referer': 'http://flight.order.qunar.com/flight/findbyorder.html',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9',
            }
            if self.RCR.request_to_post() and self.RCR.page_source != "页面异常":
                self.sign = self.DPR.parse_to_attributes('text','xpath','//input[@name="sign"]/@value',
                                                        self.RCR.page_source)[0]
                self.busiTypeID = self.DPR.parse_to_attributes('text','xpath','//input[@name="busiTypeId"]/@value',self.RCR.page_source)[0]
                self.tradeNo = self.DPR.parse_to_attributes('text','xpath','//input[@name="tradeNo"]/@value',self.RCR.page_source)[0]
                self.checkCode = self.DPR.parse_to_attributes('text','xpath','//input[@name="checkCode"]/@value',self.RCR.page_source)[0]
                self.orderDate = self.DPR.parse_to_attributes('text','xpath','//input[@name="orderDate"]/@value',self.RCR.page_source)[0]
                self.merchantCode = self.DPR.parse_to_attributes('text','xpath','//input[@name="merchantCode"]/@value',self.RCR.page_source)[0]
                self.version = self.DPR.parse_to_attributes('text','xpath','//input[@name="version"]/@value',self.RCR.page_source)[0]
                return True
            else:
                return False


    def get_details(self):
        """
        
        Returns:

        """
        self.RCR.url = 'https://order.flight.qunar.com/nts/order/orderDetail'
        self.RCR.headers = {
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Origin': 'https://order.flight.qunar.com',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Sec-Fetch-Site': 'none',
            'Referer': 'http://flight.order.qunar.com/flight/findbyorder.html',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        self.RCR.param_data = (
                ('biz', 'interNTS'),
                ('orderNo', self.CPR.record),
                ('otaType', '5'),
                ('bizType', '1'),
            )

        self.RCR.post_data = {
              'ordertoken': self.ordertoken
            }

        if self.RCR.request_to_post():
            order_no = self.DPR.parse_to_attributes('text','xpath','//div[@class="color1 '
                                                                  'order-number-item"]/span/text()',self.RCR.page_source)[0]
            dep_airport = self.DPR.parse_to_attributes('text','xpath','//div[@class="flight-info-item airport-info"]/div[1]/span[2]/text()',self.RCR.page_source)[0]
            dep_data = self.DPR.parse_to_attributes('text','xpath','//div[@class="m-content flight-main"]/div[1]/span[1]/text()',self.RCR.page_source)[0].replace('-','')
            dep_time = dep_data+self.DPR.parse_to_attributes('text','xpath','//div[@class="flight-info-item mr15"]/div[1]/text()',self.RCR.page_source)[0].replace(':','')
            arr_time = dep_data+self.DPR.parse_to_attributes('text','xpath','//div[@class="flight-info-item mr15"]/div[2]/span/text()',self.RCR.page_source)[0].replace(':','')
            air_aiport = self.DPR.parse_to_attributes('text','xpath','//div[@class="flight-info-item airport-info"]/div[3]/span[2]/text()',self.RCR.page_source)[0]
            contact = self.DPR.parse_to_attributes('text','xpath','//div[@class="contact-item"]/div[@class="contact-item-name"]/text()',self.RCR.page_source)[0]
            contact_phone = self.DPR.parse_to_attributes('text','xpath','//div[@class="contact-item"]/div[@class="contact-item-phone"]/text()',self.RCR.page_source)[0]
            contact_mail = self.DPR.parse_to_attributes('text','xpath','//div[@class="contact-item"]/div[@class="contact-item-mail"]/text()',self.RCR.page_source)[0]
            flight_number = self.DPR.parse_to_attributes('text', 'xpath', '//div[@class="flight-info"]/div[4]/div[1]/span/text()',self.RCR.page_source)[0].split(' ')[1]
            html = etree.HTML(self.RCR.page_source)
            passenger_list = html.xpath('//*[@class="m-content passenger-info-main"]/div[@class="passenger-item"]')
            self.segments.append({
                "arrivalAircode": air_aiport,
                "arrivalTime": arr_time,
                "departureAircode": dep_airport,
                "departureTime": dep_time,
                "flightNum": flight_number,
                "tripType": 1,
            })
            for i in passenger_list:
                name = i.xpath("./div/div/div[1]/span/text()")[0]
                gender = i.xpath("./div/div/div[2]/span[2]/text()")[0]
                passenger_type = i.xpath("./div[2]/div[1]/text()")[0]
                birthday = i.xpath("./div[2]/div[2]/span[2]/text()")[0].replace('-','')
                card = i.xpath("./div[3]/div[1]/span[2]/text()")[0]
                if passenger_type == "成人票":
                    passenger_type = 0
                else:
                    passenger_type = 1
                if gender == '男':
                    gender = 'M'
                else:
                    gender = 'F'
                self.passengers.append({
                    "cardExpired": card,
                    "cardType": "",
                    "identificationNumber": "",
                    "passengerBirthday": birthday,
                    "passengerName": name,
                    "passengerNationality": "",
                    "passengerSex": gender,
                    "passengerType": passenger_type,
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