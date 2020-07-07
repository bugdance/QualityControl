#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Created on Fri May 10 03:47:45 UTC+8:00 2019
    测试单元
written by pyleo.
"""
import logging
from accessor.ppeteer_crawler import PpeteerCrawler
from accessor.request_crawler import RequestCrawler
from booster.basic_parser import BasicParser
from booster.date_formatter import DateFormatter
from booster.dom_parser import DomParser
from detector.corptr_simulator import CorpTRSimulator
from hammer.data_tester import a


logger = logging.getLogger("test")
logger.setLevel(level=logging.INFO)
formatter = logging.Formatter('[%(asctime)s]%(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


if __name__ == '__main__':
    RC = RequestCrawler()
    PC = PpeteerCrawler()
    BP = BasicParser()
    DF = DateFormatter()
    DP = DomParser()
    CS = CorpTRSimulator()
    RC.logger = logger
    PC.logger = logger
    BP.logger = logger
    DF.logger = logger
    DP.logger = logger
    CS.logger = logger

    queues, temp_list = BP.parse_to_path("$..queues", a)
    changes = ["Cancelled Flight", "ScheduleTimeChange", "REFUND", "CANCEL", "CHANGE"]
    if queues:
        for i in queues:
            for k, v in i.items():
                if type(v) is str:
                    for c in changes:
                        if c.lower() in v.lower():
                            print("错误的")
                            print(k, v)
                else:
                    continue
    else:
        print("正确")
    
    
    


