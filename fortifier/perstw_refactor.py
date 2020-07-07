#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Created on 2019-09-09 11:38:21
written by pyEd.
"""
from booster.basic_parser import BasicParser
from booster.callin_parser import CallInParser
import re


class BPRefactor(BasicParser):
    """重构基础解析器
    """
    def parse_as_split(self, split_syntax: str = "", source_data: str = "") -> list:
        """解析切割
        :param split_syntax:  正则语法
        :param source_data:  来源数据
        :return:  list
        """
        if not split_syntax or not source_data or type(source_data) is not str:
            self.logger.info(f"解析替换非法传参(*>﹏<*)【{split_syntax}】")
            return []
        return re.split(split_syntax, source_data)


class CPRefactor(CallInParser):
    """重构接入解析器
    """
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
        # # # 质检不检查账户是否存在
        self.task_id = source_dict.get('orderNO')
        self.record = source_dict.get('ticketNumber')
        self.departure_code = source_dict.get('departureAircode')
        self.arrival_code = source_dict.get('arrivalAircode')
        self.departure_time = source_dict.get('departureTime')
        passenger_name = source_dict.get('passengerName')
        if not passenger_name and type(passenger_name) is not str:
            self.logger.info(f"解析数据非法乘客(*>﹏<*)【{passenger_name}】")
            return False
        passenger_name = passenger_name.split(",")
        self.passenger_name_list = []
        for i in passenger_name:
            data = {}
            name = i.split('/')
            if len(name) != 2:
                if not passenger_name and type(passenger_name) is not str:
                    self.logger.info(f"解析数据非法乘客(*>﹏<*)【{passenger_name}】")
                    return False
            data = {
                "last_name": name[0],
                "first_name": name[1]
            }
            self.passenger_name_list.append(data)
        # self.last_name = passenger_name[0]
        # self.first_name = passenger_name[1]
        return True
