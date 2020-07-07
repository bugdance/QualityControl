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
"""The parser is use for parse the data."""


class CallInParser:
    """接入解析器，解析接口结构数据。"""
    
    def __init__(self, enable_corp: bool = True):
        """Init.

        Args:
            enable_corp (bool): Whether it is a corporate account(True/False). 是否是企业账户。
        """
        self.logger: any = None  # 日志记录器。
        self.enable_corp: bool = enable_corp  # 是否是企业类型。
        # # # Interface data. 接口数据。
        self.task_id: any = None  # 任务编号。
        self.username: str = ""  # 最终用的用户名。
        self.password: str = ""  # 最终用的密码。
        self.record: str = ""  # 订单PNR
        self.first_name: str = ""  # 名字
        self.last_name: str = ""  # 姓氏
        self.departure_code: str = ""  # 始发三字码
        self.arrival_code: str = ""  # 到达三字码
        self.departure_time: str = ""  # 出发日期
        self.flight_number: str = ""  # 航班号

    def parse_to_interface(self, source_dict: dict = None) -> bool:
        """Parsing interface parameters. 解析接口数据。

        Args:
            source_dict (dict): The source dict. 来源字典。

        Returns:
            bool
        """
        if not source_dict or type(source_dict) is not dict:
            self.logger.info(f"解析接口参数有误(*>﹏<*)【{source_dict}】")
            return False
        # # # Parse the username and password. 解析账户名和密码，区分企业个人。
        account_agent = source_dict.get('carrierAccountAgent')
        account = source_dict.get('carrierAccount')
        if self.enable_corp:
            self.username = account_agent
            self.password = source_dict.get('carrierPasswordAgent')
        else:
            self.username = account
            self.password = source_dict.get('carrierPassword')
        # # # Parse the detail. 解析航班信息。
        self.task_id = source_dict.get('orderNO')
        self.record = source_dict.get('ticketNumber')
        self.departure_code = source_dict.get('departureAircode')
        self.arrival_code = source_dict.get('arrivalAircode')
        self.departure_time = source_dict.get('departureTime')
        self.flight_number = source_dict.get('flightNum')
        passenger_name = source_dict.get('passengerName')
        if not passenger_name and type(passenger_name) is not str:
            self.logger.info(f"解析数据非法乘客(*>﹏<*)【{passenger_name}】")
            return False
        passenger_name = passenger_name.split("/")
        if len(passenger_name) != 2:
            if not passenger_name and type(passenger_name) is not str:
                self.logger.info(f"解析数据非法乘客(*>﹏<*)【{passenger_name}】")
                return False
        self.last_name = passenger_name[0]
        self.first_name = passenger_name[1]
        
        return True

    def parse_to_passenger(self, passengers_list: list = None) -> bool:
        """Parse the passengers. 乘客信息解析。

        Args:
            passengers_list (list): The passengers list. 乘客列表。

        Returns:
            bool
        """
        pass