#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""Created on Fri May 10 03:47:45 UTC+8:00 2019
    模拟器用于模拟一些验证, AK模拟器
written by pyleo.
"""
import base64


class PersAKSimulator:
    """AK模拟器

    """
    def __init__(self):
        self.logger: any = None                     # 基础日志
        # # # 认证数组
        self.synonyms: dict = {
            'MCI5': 1, 'MLAK': 1, 'MBD7': 1, 'MKLB': 1, 'MCAI': 1,
            'MCX5': 2, 'MCDJ': 2, 'MEAK': 2, 'MDD7': 2, 'MAZ2': 2,
            'MEGR': 3, 'MEDJ': 3, 'MFXT': 3, 'MEQZ': 3, 'MDXT': 3,
            'MBXT': 4, 'MEZ2': 4, 'MEXT': 4, 'MEI5': 4, 'MDI5': 4,
            'MED7': 5, 'MCXJ': 5, 'MAXT': 5, 'MEFD': 5, 'MCXT': 5
        }
        # # # 认证api
        self.apis: dict = {
            'addons': 'sdlkd2l3', 'seat': 'eue3kds',
            'checkout': 'xmncx278', 'search': 'wiuwejk2',
            'available_dates': 'jksdkjsd2'
        }
        self.channel_id: str = "906a14a4c039ea4af65874742638ddae5c3ec9c6bbc9026eea35f00f"
        self.search_bearer: str = ""                # 查询认证
        self.add_bearer: str = ""                   # 附加认证
        self.check_bearer: str = ""                 # 提交认证

    def generate_to_token(self, group_num: int = 0, group_list: list = None) -> str:
        """生成令牌
        :param group_num:  标识组的id
        :param group_list:  标识组的数据
        :return:  str
        """
        try:
            add_extra = True if group_num == 2 or group_num == 5 else False
            insert = True if group_num == 3 or group_num == 4 or group_num == 5 else False
            insert_random = True if group_num == 3 else False
            reverse = True if group_num == 1 or group_num == 3 or group_num == 4 else False
            token_string = ""
            for i, v in enumerate(group_list):
                single_string = v
                if insert:
                    if (i + 1) % 3 != 0 and not insert_random:
                        continue
                    if (i + 1) % 3 == 0 and insert_random:
                        continue
                if add_extra:
                    single_string = v[:-1]
                if reverse:
                    token_string = single_string + token_string
                else:
                    token_string += single_string
            result_string = base64.b64decode(token_string).decode("utf-8")
        except Exception as ex:
            self.logger.info(f"生成令牌字符失败(*>﹏<*)【{group_num}】")
            self.logger.info(f"生成令牌失败原因(*>﹏<*)【{ex}】")
            return ""
        else:
            self.logger.info(f"生成令牌字符成功(*^__^*)【{group_num}】")
            return result_string

    def generate_to_bearer(self, token_data: list = None) -> bool:
        """生成认证
        :param token_data:  认证数据
        :return:  bool
        """
        try:
            search_source = self.apis.get('search')
            add_source = self.apis.get('addons')
            check_source = self.apis.get('checkout')
            for i in token_data:
                if i.get('source') == search_source:
                    search_group = i.get('ssrgroup')
                    search_num = self.synonyms.get(search_group)
                    search_list = i.get('ssrlist')
                    self.search_bearer = self.generate_to_token(search_num, search_list)
                elif i.get('source') == add_source:
                    add_group = i.get('ssrgroup')
                    add_num = self.synonyms.get(add_group)
                    add_list = i.get('ssrlist')
                    self.add_bearer = self.generate_to_token(add_num, add_list)
                elif i.get('source') == check_source:
                    check_group = i.get('ssrgroup')
                    check_num = self.synonyms.get(check_group)
                    check_list = i.get('ssrlist')
                    self.check_bearer = self.generate_to_token(check_num, check_list)
        except Exception as ex:
            self.logger.info(f"生成认证字符失败(*>﹏<*)【bearer】")
            self.logger.info(f"生成认证失败原因(*>﹏<*)【{ex}】")
            return False
        else:
            if self.search_bearer and self.add_bearer and self.check_bearer:
                self.logger.info("生成认证字符成功(*^__^*)【bearer】")
                return True
            else:
                self.logger.info("生成认证字符为空(*>﹏<*)【bearer】")
                return False
