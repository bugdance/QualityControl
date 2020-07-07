#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Created on Fri May 10 03:47:45 UTC+8:00 2019

written by pyleo.
"""
# # # 模拟接口
import requests

from explorer.appn5j_scraper import Appn5JScraper
from explorer.corpdd_scraper import CorpDDScraper
from explorer.corpod_scraper import CorpODScraper
from explorer.corpsl_scraper import CorpSLScraper
from explorer.corptr_scraper import CorpTRScraper
from explorer.corpuo_scraper import CorpUOScraper
from explorer.pers5j_scraper import Pers5JScraper
from explorer.persak_scraper import PersAKScraper
from explorer.persbc_scraper import PersBCScraper
from explorer.persjq_scraper import PersJQScraper
from explorer.persmm_scraper import PersMMScraper
from explorer.persnk_scraper import PersNKScraper
from explorer.persqn_scraper import PersQNScraper
from explorer.perstt_scraper import PersTTScraper
from explorer.perstw_scraper import PersTWScraper
from explorer.persu2_scraper import PersU2Scraper
from explorer.persvy_scraper import PersVYScraper
from explorer.perswn_scraper import PersWNScraper
from explorer.persxw_scraper import PersXWScraper





orderNO = 111111
carrierAccount = "168033518@qq.com"
carrierPassword = "Su123456"
carrierAccountAgent = "QCYG014"
carrierPasswordAgent = "Hthy@1234"
ticketNumber = "V5KD3S"
passengerName = "LI/LIYAO"
departureAircode = "SIN"
arrivalAircode = "XIY"
departureTime = "2019-10-28"


post_data = {'carrierAccount': carrierAccount, 'carrierPassword': carrierPassword,
            "carrierAccountAgent": carrierAccountAgent, "carrierPasswordAgent": carrierPasswordAgent,
            "orderNO": orderNO, "ticketNumber": ticketNumber, "passengerName": passengerName,
            "departureAircode": departureAircode, "arrivalAircode": arrivalAircode,
             "departureTime": departureTime
        }

post_data = {'departureTime': '2020-05-08', 'ticketNumber': 'SX7NHR', 'passengerName': 'GUO/CHAOHUI', 'orderNO': 189277, 'carrierPasswordAgent': '', 'arrivalAircode': 'KIX', 'carrierAccountAgent': '', 'carrierAccount': '', 'departureAircode': 'PVG', 'carrierPassword': ''}



def post_test():
    """
    :return:
    """
    account = "pers"
    company = "tr"
    url = f"http://interface.python.flight.yeebooking.com/quality/{company}/"
    # url = f"http://119.3.169.64:18081/quality/{company}/"
    # url = f"http://45.81.129.30:18081/quality/{company}/"
    response = requests.post(url=url, json=post_data)
    print(response.text)


if __name__ == '__main__':
    post_test()
    # process_dict = {
    #     "task_id": 1111, "log_path": "test.log", "source_dict": post_data,
    #     "enable_proxy": False, "address": "http://127.0.0.1:9000", "retry_count": 1
    # }
    #
    # airline_account = "appn"
    # airline_company = "5j"
    # create_var = locals()
    # scraper = create_var[airline_account.capitalize() + airline_company.upper() + "Scraper"]()
    # result = scraper.process_to_main(process_dict)




