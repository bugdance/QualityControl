#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Created on Fri May 10 03:47:45 UTC+8:00 2019
    镜像器用于存储稳定的数据, BC镜像器
written by pyleo.
"""


class PersBCMirror:
    """BC镜像器
    """
    def __init__(self):
        self.logger: any = None  # 日志记录器
        # # # 国家三字码
        self._country_code: dict = {
            'HND': 'Haneda',
            'CTS': 'Sapporo(New Chitose)',
            'SDJ': 'Sendai',
            'IBR': 'Ibaraki',
            'NGO': 'Nagoya(Chubu)',
            'UKB': 'Kobe',
            'FUK': 'Fukuoka',
            'NGS': 'Nagasaki',
            'KOJ': 'Kagoshima',
            'ASJ': 'Amamioshima',
            'OKA': 'Naha'
        }
