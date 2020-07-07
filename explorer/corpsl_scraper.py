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
from collector.corpsl_mirror import CorpSLMirror
from detector.corpsl_simulator import CorpSLSimulator


class CorpSLScraper(RequestWorker):
    """SL采集器, 账号和首页对比

    """

    def __init__(self) -> None:
        RequestWorker.__init__(self)
        self.RCR = RequestCrawler()  # 请求爬行器。
        self.AFR = AESFormatter()  # AES格式器。
        self.BFR = BasicFormatter()  # 基础格式器。
        self.BPR = BasicParser()  # 基础解析器。
        self.CFR = CallBackFormatter()  # 回调格式器。
        self.CPR = CallInParser()  # 接入解析器。
        self.DFR = DateFormatter()  # 日期格式器。
        self.DPR = DomParser()  # 文档解析器。
        self.CMR = CorpSLMirror()  # SL镜像器。
        self.CSR = CorpSLSimulator()  # SL模拟器。
        # # # 请求中用到的变量
        self.login_source: str = ""  # 登录源数据
        self.home_source: str = ""  # 首页源数据
        self.user_url: str = ""
        
        self.captcha_num: str = ""  # 打码数字
        self.login_target: str = ""  # 登录t
        self.user_hdn: str = ""  # 登录user hdn
        # # # 返回中用到的变量
        self.order_status: str = ""  # 订单状态
        self.segments: list = []  # 航段信息
        self.passengers: list = []  # 乘客信息
        self.baggage: dict = {}

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
        self.CMR.logger = self.logger
        self.CSR.logger = self.logger
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
        if self.process_to_verify():
            if self.process_to_search():
                if self.process_to_index():
                    if self.process_to_service():
                        if self.process_to_segment():
                            if self.process_to_detail():
                                self.process_to_return()
                                self.process_to_logout(max_count=self.retry_count)
                                self.logger.removeHandler(self.handler)
                                return self.callback_data
        # # # 错误返回。
        self.callback_data['msg'] = self.callback_msg
        # self.callback_data['msg'] = "质检失败，解决问题中，请人工质检。"
        self.logger.info(self.callback_data)
        self.process_to_logout(max_count=self.retry_count)
        self.logger.removeHandler(self.handler)
        return self.callback_data

    def process_to_verify(self, count: int = 0, max_count: int = 3) -> bool:
        """Verify process. 验证过程。

		Args:
			count (int): 累计计数。
			max_count (int): 最大计数。

		Returns:
			bool
		"""
        if count >= max_count:
            return False
        else:
            if not self.CPR.username:
                self.logger.info(f"企业账户是空(*>﹏<*)【{self.CPR.username}】")
                self.callback_msg = "企业账户是空"
                return False
            # # # 爬取登录首页。
            self.RCR.url = "https://agent.lionairthai.com/b2badmin/login.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Host": "agent.lionairthai.com",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 解析首页获取打码地址，并保存首页源代码。
                self.RCR.copy_source = self.BFR.format_to_same(self.RCR.page_source)
                captcha, temp_list = self.DPR.parse_to_attributes(
                    "src", "css", "#ucAgentLogin_rdCapImage_CaptchaImageUP", self.RCR.page_source)
                if captcha:
                    # # # 爬取打码图片
                    self.RCR.url = captcha.replace("..", "https://agent.lionairthai.com")
                    self.RCR.param_data = None
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
                        "Host": "agent.lionairthai.com",
                        "Referer": "https://agent.lionairthai.com/b2badmin/login.aspx"
                    })
                    if self.RCR.request_to_get("content"):
                        captcha_page = self.BFR.format_to_same(self.RCR.page_source)
                        # # # 先进行接口打码
                        self.RCR.timeout = 5
                        self.RCR.url = "http://119.3.234.171:33333/captcha/sl/"
                        self.RCR.param_data = None
                        self.RCR.header = None
                        self.RCR.post_data = {"img": self.RCR.page_source}
                        if self.RCR.request_to_post("files", "json"):
                            self.captcha_num = self.RCR.page_source.get('result')
                        else:
                            # # # 失败则进行自定义打码
                            code_string = self.CSR.recognize_to_captcha("img/cap.jpg", captcha_page)
                            code_regex, code_list = self.BPR.parse_to_regex("\d+", code_string)
                            if code_list:
                                code_all = ""
                                for i in code_list:
                                    code_all += i
                                self.captcha_num = code_all
                        self.RCR.timeout = 25
                        # # # 判断打码准确性
                        if len(self.captcha_num) != 6:
                            self.logger.info(f"打码认证数字失败(*>﹏<*)【{self.captcha_num}】")
                            self.callback_msg = f"请求认证第{count + 1}次失败"
                            return self.process_to_verify(count + 1, max_count)
                        else:
                            # # # 判断是否需要重新打码
                            self.logger.info(f"打码图片数字成功(*^__^*)【{self.captcha_num}】")
                            if self.process_to_login():
                                return True
                            else:
                                if "enter a valid verification code" not in self.callback_msg:
                                    return False
                                else:
                                    self.logger.info(f"打码认证返回无效(*>﹏<*)【{self.captcha_num}】")
                                    self.callback_msg = f"请求认证第{count + 1}次失败"
                                    return self.process_to_verify(count + 1, max_count)
            # # # 错误重试。
            self.logger.info(f"请求认证第{count + 1}次失败(*>﹏<*)【verify】")
            self.callback_msg = f"请求认证第{count + 1}次失败"
            return self.process_to_verify(count + 1, max_count)

    def process_to_login(self, count: int = 0, max_count: int = 2) -> bool:
        """Login process. 登录过程。

		Args:
			count (int): 累计计数。
			max_count (int): 最大计数。

		Returns:
			bool
		"""
        if count >= max_count:
            return False
        else:
            # # # 解析登录首页
            self.RCR.url = "https://agent.lionairthai.com/b2badmin/login.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Host": "agent.lionairthai.com",
                "Origin": "https://agent.lionairthai.com",
                "Referer": "https://agent.lionairthai.com/b2badmin/login.aspx",
                "X-MicrosoftAjax": "Delta=true",
                "X-Requested-With": "XMLHttpRequest"
            })
            # # # 拼接请求参数
            login_rad, temp_list = self.BPR.parse_to_regex('%3b%3bSystem.Web.Extensions.*?"', self.RCR.copy_source)
            login_rad = login_rad.strip('"')
            self.user_hdn, temp_list = self.DPR.parse_to_attributes(
                "value", "css", "#hdnCustomerUserID", self.RCR.copy_source)
            password = self.CPR.password
            param_batch = [
                ("ucAgentLogin$RadScrMgr", False, "ucAgentLogin$UpdatePanel1|ucAgentLogin$btnLogin"),
                ("__LASTFOCUS", True, "#__LASTFOCUS"), ("ucAgentLogin_RadScrMgr_TSM", False, login_rad),
                ("__EVENTTARGET", True, "#__EVENTTARGET"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"), ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                ("__EVENTVALIDATION", True, "#__EVENTVALIDATION"), ("hdnCustomerUserID", False, self.user_hdn),
                ("hdnLangCode", True, "#hdnLangCode"),
                ("ucAgentLogin$hdfCustomerUserID", True, "#ucAgentLogin_hdfCustomerUserID"),
                ("ucAgentLogin$txtUserName", False, self.CPR.username),
                ("ucAgentLogin$txtPassword", False, password),
                ("ucAgentLogin$rdCapImage$CaptchaTextBox", False, self.captcha_num),
                ("ucAgentLogin_rdCapImage_ClientState", True, "#ucAgentLogin_rdCapImage_ClientState"),
                ("ucAgentLogin$cssversion", True, "#ucAgentLogin_cssversion"), ("__ASYNCPOST", False, "true"),
                ("ucAgentLogin$btnLogin", True, "#ucAgentLogin_btnLogin"),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.copy_source)
            if self.RCR.request_to_post():
                # # # 解析登录后状态，判断是否成功
                error_message, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "#ucAgentLogin_lblMessage", self.RCR.page_source)
                if error_message:
                    error_message = self.BPR.parse_to_separate(error_message)
                    if "already in Use" in error_message:
                        self.logger.info(f"账户已被他人占用(*>﹏<*)【{error_message}】")
                        self.callback_msg = "账户已被他人占用"
                        return False
                    else:
                        self.logger.info(f"用户请求登录失败(*>﹏<*)【{error_message}】")
                        self.callback_msg = f"{error_message}"
                        return False
                else:
                    # # # 获取用户访问状态t=id
                    b2b_admin, temp_list = self.BPR.parse_to_regex("B2BAdmin.*?\\|", self.RCR.page_source)
                    login_target, temp_list = self.BPR.parse_to_regex("%3d.*", b2b_admin)
                    if not login_target or len(login_target) <= 4:
                        self.logger.info("匹配用户状态失败(*>﹏<*)【login】")
                        self.callback_msg = "匹配用户状态失败"
                        return self.process_to_login(count + 1, max_count)
                    else:
                        self.login_target = login_target[3:-1]
                        # # # 爬取登录后控制面板页
                        self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx"
                        self.RCR.param_data = (("t", self.login_target),)
                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                        self.RCR.header.update({
                            "Host": "agent.lionairthai.com",
                            "Referer": "https://agent.lionairthai.com/b2badmin/login.aspx",
                            "Upgrade-Insecure-Requests": "1"
                        })
                        if self.RCR.request_to_get(is_redirect=True):
                            self.RCR.copy_source = self.BFR.format_to_same(self.RCR.page_source)
                            return True
            # # # 错误重试。
            self.logger.info(f"请求登录第{count + 1}次失败(*>﹏<*)【login】")
            self.callback_msg = f"请求登录第{count + 1}次失败"
            return self.process_to_login(count + 1, max_count)

    def process_to_logout(self, count: int = 0, max_count: int = 2) -> bool:
        """Logout process. 退出过程。

		Args:
			count (int): 累计计数。
			max_count (int): 最大计数。

		Returns:
			bool
		"""
        if count >= max_count:
            return False
        else:
            # # # 解析登录，认证
            if not self.process_to_verify():
                return False
            else:
                # # # 解析退出页面
                self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx"
                self.RCR.param_data = (("t", self.login_target),)
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Host": "agent.lionairthai.com",
                    "Origin": "https://agent.lionairthai.com",
                    "Referer": f"https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx?t={self.login_target}"
                })
                # # # 拼接参数，解析退出
                logout_rad, temp_list = self.BPR.parse_to_regex(
                    '%3b%3bSystem.Web.Extensions.*?"', self.RCR.copy_source)
                logout_rad = logout_rad.strip('"')
                param_batch = [
                    ("RadScriptManager1_TSM", False, logout_rad),
                    ("__EVENTTARGET", False, "ctl00$btnLogout"),
                    ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                    ("__VIEWSTATE", True, "#__VIEWSTATE"),
                    ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                    ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                    ("ctl00$bodycontent$txtSearch", False, ""),
                    ("ctl00$bodycontent$hdnphSearch", False, "Search+Here..."),
                    ("ctl00$bodycontent$hdnPopupShown", False, "True"),
                ]
                # # # 拼接每个页面具体的参数id
                mnu_id, mnu_list = self.DPR.parse_to_attributes(
                    "id", "css", "input[id*=lstmenudisplay_mnuId]", self.RCR.copy_source)
                if mnu_list:
                    for i in range(len(mnu_list)):
                        param_batch.extend([
                            (f"ctl00$lstmenudisplay$ctrl{i}$mnuId", True, f"#lstmenudisplay_mnuId_{i}"),
                            (f"ctl00$lstmenudisplay$ctrl{i}$hdfPageName", True, f"#lstmenudisplay_hdfPageName_{i}"),
                        ])
                self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.copy_source)
                if self.RCR.request_to_post(status_code=302):
                    # # # 爬取退出后页面确认状态
                    self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx"
                    self.RCR.param_data = (("t", self.login_target),)
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Host": "agent.lionairthai.com",
                        "Origin": "https://agent.lionairthai.com",
                        "Referer": f"https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx?t={self.login_target}"
                    })
                    if self.RCR.request_to_get(status_code=302):
                        return True
            # # # 错误重试。
            self.logger.info(f"请求退出第{count + 1}次失败(*>﹏<*)【logout】")
            self.callback_msg = f"请求退出第{count + 1}次失败"
            return self.process_to_logout(count + 1, max_count)
    
    def process_to_search(self, count: int = 0, max_count: int = 2) -> bool:
        """登录后查询航班流程
        :return:  bool
        """
        if count >= max_count:
            return False
        else:
            # # # 请求列表页面
            self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/PassengerSearchList.aspx"
            self.RCR.param_data = (("t", self.login_target),)
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Host": "agent.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx?t={self.login_target}"
            })
            if self.RCR.request_to_get():
                # # # 请求具体某个订单
                self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/PassengerSearchList.aspx"
                self.RCR.param_data = (("t", self.login_target),)
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "*/*",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Host": "agent.lionairthai.com",
                    "Origin": "https://agent.lionairthai.com",
                    "X-MicrosoftAjax": "delta=true",
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"https://agent.lionairthai.com/B2BAdmin/PassengerSearchList.aspx?t={self.login_target}"
                })
                # # # 拼接请求参数
                search_rad, temp_list = self.BPR.parse_to_regex('%3b%3bSystem.Web.Extensions.*?"', self.RCR.page_source)
                search_rad = search_rad.strip('"')
                param_batch = [
                    ("ctl00$RadScriptManager1", False, "ctl00$bodycontent$upRequest|ctl00$bodycontent$btnSearch"),
                    ("RadScriptManager1_TSM", False, search_rad),
                    ("__EVENTTARGET", True, "#__EVENTTARGET"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                    ("__VIEWSTATE", True, "#__VIEWSTATE"), ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                    ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                    ("__EVENTVALIDATION", True, "#__EVENTVALIDATION"),
                ]
                # # # 拼接每个页面具体的参数id
                mnu_id, mnu_list = self.DPR.parse_to_attributes(
                    "id", "css", "input[id*=lstmenudisplay_mnuId]", self.RCR.page_source)
                if mnu_list:
                    for i in range(len(mnu_list)):
                        param_batch.extend([
                            (f"ctl00$lstmenudisplay$ctrl{i}$mnuId", True, f"#lstmenudisplay_mnuId_{i}"),
                            (f"ctl00$lstmenudisplay$ctrl{i}$hdfPageName", True, f"#lstmenudisplay_hdfPageName_{i}"),
                        ])
                # # # 拼接查询范围
                from_date = self.DFR.format_to_now(custom_days=-365)
                to_date = self.DFR.format_to_now()
                from_single = f"{from_date.year},{from_date.month},{from_date.day}"
                from_year = from_date.strftime("%Y-%m-%d")
                from_input = from_date.strftime("%d-%b-%Y")
                to_single = f"{to_date.year},{to_date.month},{to_date.day}"
                to_year = to_date.strftime("%Y-%m-%d")
                to_input = to_date.strftime("%d-%b-%Y")
                
                param_batch.extend([
                    ("ctl00$bodycontent$txtReservationID", False, self.CPR.record),
                    ("ctl00$bodycontent$txtPaxName", False, ""),
                    ("ctl00$bodycontent$dpReservationFrom", True, "#ctl00_bodycontent_dpReservationFrom"),
                    ("ctl00$bodycontent$dpReservationFrom$dateInput", True, "#ctl00_bodycontent_dpReservationFrom_dateInput"),
                    ("ctl00_bodycontent_dpReservationFrom_dateInput_ClientState", False,
                     '{"enabled":true,"emptyMessage":"","validationText":"","valueAsString":"",'
                     '"minDateStr":"1980-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":""}'
                     ),
                    ("ctl00_bodycontent_dpReservationFrom_calendar_SD", False, "[]"),
                    ("ctl00_bodycontent_dpReservationFrom_calendar_AD", False, f"[[1980,1,1],[2099,12,30],[{to_single}]]"),
                    ("ctl00_bodycontent_dpReservationFrom_ClientState", True, "#ctl00_bodycontent_dpReservationFrom_ClientState"),
                    ("ctl00$bodycontent$dtBookingDateFrom", False, from_year),
                    ("ctl00$bodycontent$dtBookingDateFrom$dateInput", False, from_input),
                    ("ctl00_bodycontent_dtBookingDateFrom_dateInput_ClientState", False,
                     f'{{"enabled":true,"emptyMessage":"","validationText":"{from_year}-00-00-00",'
                     f'"valueAsString":"{from_year}-00-00-00","minDateStr":"1980-01-01-00-00-00",'
                     f'"maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"{from_input}"}}'
                     ),
                    ("ctl00_bodycontent_dtBookingDateFrom_calendar_SD", False, f"[[{to_single}]]"),
                    ("ctl00_bodycontent_dtBookingDateFrom_calendar_AD", False, f"[[1980,1,1],[2099,12,30],[{from_date.year},{from_date.month},1]]"),
                    ("ctl00_bodycontent_dtBookingDateFrom_ClientState", True, "#ctl00_bodycontent_dtBookingDateFrom_ClientState"),
                    ("ctl00$bodycontent$dtBookingDateTo", False, to_year),
                    ("ctl00$bodycontent$dtBookingDateTo$dateInput", False, to_input),
                    ("ctl00_bodycontent_dtBookingDateTo_dateInput_ClientState", False,
                     f'{{"enabled":true,"emptyMessage":"","validationText":"{to_year}-00-00-00",'
                     f'"valueAsString":"{to_year}-00-00-00","minDateStr":"{from_year}-00-00-00",'
                     f'"maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":"{to_input}"}}'
                     ),
                    ("ctl00_bodycontent_dtBookingDateTo_calendar_SD", False, "[]"),
                    ("ctl00_bodycontent_dtBookingDateTo_calendar_AD", False, f"[[{from_single}],[2099,12,30],[{to_single}]]"),
                    ("ctl00_bodycontent_dtBookingDateTo_ClientState", False,
                     f'{{"minDateStr":"{from_year}-00-00-00","maxDateStr":"2099-12-31-00-00-00"}}'),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$FilterTextBox_ReservationID",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_FilterTextBox_ReservationID"),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$FilterTextBox_PNRNo",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_FilterTextBox_PNRNo"),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$FilterTextBox_ReservationType",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_FilterTextBox_ReservationType"),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$FilterTextBox_PassengerName",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_FilterTextBox_PassengerName"),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$FilterTextBox_SellingCurrency",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_FilterTextBox_SellingCurrency"),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$RDIPFReservationDate",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFReservationDate"),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$RDIPFReservationDate$dateInput",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFReservationDate_dateInput"),
                    ("ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFReservationDate_dateInput_ClientState", False,
                     '{"enabled":true,"emptyMessage":"","validationText":"","valueAsString":"",'
                     '"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":""}'
                     ),
                    ("ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFReservationDate_ClientState", False,
                     '{"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}'),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$RDIPFTicketingDeadline",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFTicketingDeadline"),
                    ("ctl00$bodycontent$RGUserList$ctl00$ctl02$ctl02$RDIPFTicketingDeadline$dateInput",
                     True, "#ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFTicketingDeadline_dateInput"),
                    ("ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFTicketingDeadline_dateInput_ClientState", False,
                     '{"enabled":true,"emptyMessage":"","validationText":"","valueAsString":"",'
                     '"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00","lastSetTextBoxValue":""}'),
                    ("ctl00_bodycontent_RGUserList_ctl00_ctl02_ctl02_RDIPFTicketingDeadline_ClientState", False,
                     '{"minDateStr":"1900-01-01-00-00-00","maxDateStr":"2099-12-31-00-00-00"}'),
                    ("ctl00_bodycontent_RGUserList_rfltMenu_ClientState", True, "#ctl00_bodycontent_RGUserList_rfltMenu_ClientState"),
                    ("ctl00_bodycontent_RGUserList_gdtcSharedCalendar_SD", False, "[]"),
                    ("ctl00_bodycontent_RGUserList_gdtcSharedCalendar_AD", False, f'[[1900,1,1],[2099,12,31],[{to_single}]]'),
                    ("ctl00_bodycontent_RGUserList_ClientState", True, "#ctl00_bodycontent_RGUserList_ClientState"),
                    ("__ASYNCPOST", False, "true"), ("ctl00$bodycontent$btnSearch", False, "Search"),
                ])
                self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.page_source)
                if self.RCR.request_to_post():
                    # # # 查询错误信息
                    error_message, temp_list = self.DPR.parse_to_attributes(
                        "text", "css", "#bodycontent_lblErrorMsgs", self.RCR.page_source)
                    if error_message:
                        self.logger.info(error_message)
                        self.callback_msg = error_message
                        return False
                    # # # 查询订单具体sid
                    sid, temp_list = self.DPR.parse_to_attributes(
                        "text", "css", "#ctl00_bodycontent_RGUserList_ctl00__0 td:first-child", self.RCR.page_source)
                    self.order_status, temp_list = self.DPR.parse_to_attributes(
                        "text", "css", "#ctl00_bodycontent_RGUserList_ctl00__0 td:nth-child(9)", self.RCR.page_source)
                    if not sid:
                        self.logger.info("查询不到具体订单(*>﹏<*)【query】")
                        self.callback_msg = "查询不到具体订单"
                        return False
                    # # # 请求详细页面
                    self.RCR.url = "https://agent.lionairthai.com/B2BAdmin/PassengerSearch.aspx"
                    self.RCR.param_data = (("sid", sid), ("t", self.login_target),)
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Host": "agent.lionairthai.com",
                        "Referer": f"https://agent.lionairthai.com/B2BAdmin/PassengerSearchList.aspx?t={self.login_target}"
                    })
                    if self.RCR.request_to_get():
                        # # # 保存登录后数据
                        self.login_source = self.BFR.format_to_same(self.RCR.page_source)
                        return True
            # # # 错误重试。
            self.logger.info(f"请求搜索第{count + 1}次失败(*>﹏<*)【search】")
            self.callback_msg = f"请求搜索第{count + 1}次失败"
            return self.process_to_search(count + 1, max_count)
    
    def process_to_index(self, count: int = 0, max_count: int = 2) -> bool:
        """首页查询航班流程
        :return:  bool
        """
        if count >= max_count:
            return False
        else:
            # # # 解析首页
            self.RCR.url = "https://www.lionairthai.com/en/"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Host": "www.lionairthai.com",
                "Referer": f"https://agent.lionairthai.com/B2BAdmin/DashBoard.aspx?t={self.login_target}",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 查询首页订单
                self.RCR.url = "https://search.lionairthai.com/sl/onlineaddonbooking.aspx"
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Host": "search.lionairthai.com",
                    "Origin": "https://www.lionairthai.com",
                    "Referer": f"https://www.lionairthai.com/en/",
                    "Upgrade-Insecure-Requests": "1"
                })
                self.RCR.post_data = [
                    ("opr", self.CPR.record), ("ofn", self.CPR.first_name), ("oln", self.CPR.last_name),
                ]
                if self.RCR.request_to_post(status_code=302):
                    # # 解析跳转
                    url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                    self.RCR.url = "https://search.lionairthai.com" + url
                    self.RCR.param_data = None
                    self.RCR.header = self.BFR.format_to_same(self.init_header)
                    self.RCR.header.update({
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                        "Host": "search.lionairthai.com",
                        "Referer": f"https://www.lionairthai.com/en/",
                        "Upgrade-Insecure-Requests": "1"
                    })
                    if self.RCR.request_to_get(status_code=302):
                        error, temp_list = self.DPR.parse_to_attributes(
                            "text", "css", "#divErrorMsg div[class*=errorMsg]", self.RCR.page_source)
                        error = self.BPR.parse_to_separate(error)
                        if error:
                            self.logger.info(f"请求首页失败(*>﹏<*)【{error}】")
                            self.callback_msg = error
                            return False
                        
                        # # # 解析跳转
                        url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                        self.RCR.url = "https://search.lionairthai.com" + url
                        self.RCR.param_data = None
                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                        self.RCR.header.update({
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                            "Host": "search.lionairthai.com",
                            "Referer": f"https://www.lionairthai.com/en/",
                            "Upgrade-Insecure-Requests": "1"
                        })
                        if self.RCR.request_to_get(status_code=302):
                            # # # 解析跳转
                            url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                            self.RCR.url = "https://search.lionairthai.com" + url
                            self.RCR.param_data = None
                            self.RCR.header = self.BFR.format_to_same(self.init_header)
                            self.RCR.header.update({
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                                "Host": "search.lionairthai.com",
                                "Referer": "https://www.lionairthai.com/en/",
                                "Upgrade-Insecure-Requests": "1"
                            })
                            if self.RCR.request_to_get():
                                # # # 保存首页后数据
                                self.home_source = self.BFR.format_to_same(self.RCR.page_source)
                                # # # 请求行李页面
                                self.user_url = "https://search.lionairthai.com" + url
                                return True
            # # # 错误重试。
            self.logger.info(f"请求首页第{count + 1}次失败(*>﹏<*)【index】")
            self.callback_msg = f"请求首页第{count + 1}次失败"
            return self.process_to_index(count + 1, max_count)
    
    def process_to_service(self, count: int = 0, max_count: int = 2) -> bool:
        """
        
        Returns:

        """
        if count >= max_count:
            return False
        else:
            self.RCR.url = self.user_url
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "search.lionairthai.com",
                "Origin": "https://search.lionairthai.com",
                "Referer": self.user_url,
                "Upgrade-Insecure-Requests": "1"
            })
            param_batch = [
                ("__EVENTTARGET", True, "#__EVENTTARGET"), ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"), ("__VIEWSTATEGENERATOR", True, "#__VIEWSTATEGENERATOR"),
                ("__VIEWSTATEENCRYPTED", True, "#__VIEWSTATEENCRYPTED"),
                ("__EVENTVALIDATION", True, "#__EVENTVALIDATION"),
                ("ctl00$hdnRelativePath", True, "#hdnRelativePath"),
                ("ctl00$bodycontent$hfNewRetrive", True, "#bodycontent_hfNewRetrive"),
                ("ctl00$bodycontent$hfConfrimMsg", True, "#bodycontent_hfConfrimMsg"),
                ("ctl00$bodycontent$hfPlsAgree", True, "#bodycontent_hfPlsAgree"),
                ("ctl00$bodycontent$hfPaymentFailed", True, "#bodycontent_hfPaymentFailed"),
                ("ctl00$bodycontent$btnAddOnBaggaes", True, "#bodycontent_btnAddOnBaggaes"),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.home_source)
            if self.RCR.request_to_post(status_code=302):
                url, temp_list = self.DPR.parse_to_attributes("href", "css", "a", self.RCR.page_source)
                self.RCR.url = "https://search.lionairthai.com" + url
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                    "Host": "search.lionairthai.com",
                    "Referer": self.user_url,
                    "Upgrade-Insecure-Requests": "1"
                })
                if self.RCR.request_to_get():
                    temp_source, temp_list = self.BPR.parse_to_regex("<!DOCTYPE.*", self.RCR.page_source)
                    
                    passenger, passenger_list = self.DPR.parse_to_attributes(
                        "id", "css", "div[id*='_divPaxBaggageInformation_']", temp_source)
                    if passenger_list:
                        for n, v in enumerate(passenger_list):
                            name, temp_list = self.DPR.parse_to_attributes(
                                "text", "css", f"#{v} p", temp_source)
                            name = self.BPR.parse_to_separate(name)
                            name = name.split(" ")
                            if len(name) >= 3:
                                last_name = name[-1]
                                first_all = name[1:-1]
                                first_name = ""
                                for i in first_all:
                                    first_name += i + " "
                                first_name = first_name.strip()
                                name = f"{last_name}/{first_name}"
                            
                            baggage, temp_list = self.DPR.parse_to_attributes(
                                "value", "css", f"#{v} select[id*='PaxddlOBBaggages0_0_0'] option[selected='selected']",
                                temp_source)
                            baggage, temp_list = self.BPR.parse_to_regex("\d+", baggage)
                            baggage = self.BFR.format_to_int(baggage)
                            
                            self.baggage[name] = baggage
                        
                        return True
            # # # 错误重试。
            self.logger.info(f"请求行李第{count + 1}次失败(*>﹏<*)【service】")
            self.callback_msg = f"请求行李第{count + 1}次失败"
            return self.process_to_service(count + 1, max_count)
    
    def process_to_segment(self) -> bool:
        """收集航段信息
        :return:  bool
        """
        # # # 解析俩个页面航段数量并判断是否相等
        login_flight, login_list = self.DPR.parse_to_attributes(
            "id", "css", "tr[id*=ctl00_bodycontent_RGFlightItinerary_ctl00__]", self.login_source)
        home_flight, home_list = self.DPR.parse_to_attributes(
            "class", "css", "#tblflightdetails>tbody>tr>td:nth-child(1)", self.home_source)
        
        if login_list and home_list and len(home_list) == len(login_list):
            # # # 循环航段并抓取信息
            for i in range(len(login_list)):
                # # # 解析始发站和终点站
                departure_code, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGFlightItinerary_ctl00__{i}>td:nth-child(5)",
                    self.login_source)
                departure_code, temp_list = self.BPR.parse_to_regex("\(.*\)", departure_code)
                departure_code, temp_list = self.BPR.parse_to_regex("[A-Z]+", departure_code)
                
                arrival_code, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGFlightItinerary_ctl00__{i}>td:nth-child(7)", self.login_source)
                arrival_code, temp_list = self.BPR.parse_to_regex("\(.*\)", arrival_code)
                arrival_code, temp_list = self.BPR.parse_to_regex("[A-Z]+", arrival_code)
                # # # 解析俩个页面航班号，并判断是否相等
                login_number, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGFlightItinerary_ctl00__{i}>td:nth-child(4)", self.login_source)
                login_number = login_number.replace(" ", "")
                login_code, temp_list = self.BPR.parse_to_regex("[A-Z]+", login_number)
                login_num, temp_list = self.BPR.parse_to_regex("\d+", login_number)
                login_num = self.BFR.format_to_int(login_num)
                login_number = f"{login_code}{login_num}"
                
                home_number, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath", f"//*[@id='tblflightdetails']//tbody//tr[{i + 1}]//td[1]/text()[2]",
                    self.home_source)
                home_code, temp_list = self.BPR.parse_to_regex("[A-Z]+", home_number)
                home_num, temp_list = self.BPR.parse_to_regex("\d+", home_number)
                home_num = self.BFR.format_to_int(home_num)
                home_number = f"{home_code}{home_num}"
                
                if home_number != login_number:
                    self.logger.info(f"首页航班匹配不一致(*>﹏<*)【{home_number}】【{login_number}】")
                    self.callback_msg = "首页航班匹配不一致"
                    return False
                # # # 解析俩个页面起飞时间，并判断是否相等
                login_departure, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGFlightItinerary_ctl00__{i}>td:nth-child(9)", self.login_source)
                login_departure = self.DFR.format_to_transform(login_departure, '%d-%b-%Y %H:%M')
                login_departure = login_departure.strftime("%Y%m%d%H%M")
                
                home_departure, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#tblflightdetails>tbody>tr:nth-child({i + 1})>td:nth-child(2)>span", self.home_source)
                home_departure = self.BPR.parse_to_separate(home_departure)
                
                home_departure = self.DFR.format_to_transform(home_departure, '%d-%b-%Y %H:%M')
                home_departure = home_departure.strftime("%Y%m%d%H%M")
                
                if home_departure != login_departure:
                    self.logger.info(f"首页时间匹配不一致(*>﹏<*)【{home_departure}】【{login_departure}】")
                    self.callback_msg = "首页时间匹配不一致"
                    return False
                # # # 解析首页达到时间
                home_arrival, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#tblflightdetails>tbody>tr:nth-child({i + 1})>td:nth-child(3)>span", self.home_source)
                home_arrival = self.BPR.parse_to_separate(home_arrival)
                
                home_arrival = self.DFR.format_to_transform(home_arrival, '%d-%b-%Y %H:%M')
                home_arrival = home_arrival.strftime("%Y%m%d%H%M")
                
                self.segments.append({
                    "departureAircode": departure_code, "arrivalAircode": arrival_code, "flightNum": login_number,
                    "departureTime": login_departure, "arrivalTime": home_arrival, "tripType": i + 1
                })
            
            return True
        self.logger.info("解析航段失败(*>﹏<*)【segment】")
        self.callback_msg = "解析航段失败"
        return False
    
    def process_to_detail(self) -> bool:
        """收集乘客信息
        :return:  bool
        """
        # # # 解析俩个页面乘客信息并判断是否相等
        login_passengers, login_list = self.DPR.parse_to_attributes(
            "id", "css", "tr[id*=ctl00_bodycontent_RGUserList_ctl00__]", self.login_source)
        
        home_passengers, home_list = self.DPR.parse_to_attributes(
            "class", "css", "#tblpassengers>tbody>tr>td:nth-child(1)", self.home_source)
        
        if login_list and home_list:
            for i in range(len(login_list)):
                # # # 解析俩个页面乘客类型，并判断是否相等
                login_type, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGUserList_ctl00__{i}>td:nth-child(4)", self.login_source)
                
                home_type, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#tblpassengers>tbody>tr:nth-child({i + 1})>td:nth-child(3)", self.home_source)
                home_type = self.BPR.parse_to_separate(home_type)
                
                if "Adult" in login_type and "Adult" in home_type:
                    age_type = 0
                elif "Child" in login_type and "Child" in home_type:
                    age_type = 1
                else:
                    self.logger.info(f"首页乘客匹配不一致(*>﹏<*)【{home_type}】【{login_type}】")
                    self.callback_msg = "首页乘客匹配不一致"
                    return False
                # # # 解析俩个页面乘客性别，并判断是否相等
                sex = "M"
                title, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGUserList_ctl00__{i}>td:first-child", self.login_source)
                login_last, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGUserList_ctl00__{i}>td:nth-child(3)", self.login_source)
                login_first, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGUserList_ctl00__{i}>td:nth-child(2)", self.login_source)
                
                full_name, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#tblpassengers>tbody>tr:nth-child({i + 1})>td:nth-child(2)", self.home_source)
                full_name = self.BPR.parse_to_separate(full_name)
                full_name = full_name.split(" ")
                
                home_last = ""
                home_first = ""
                if len(full_name) >= 3:
                    home_last = full_name[-1]
                    home_list = full_name[1:-1]
                    for n in home_list:
                        home_first += n + " "
                    home_first = home_first.strip()
                    
                    if age_type == 0:
                        if "Mr." == title or "MR" == title:
                            if "MR" == full_name[0]:
                                sex = "M"
                            else:
                                self.logger.info(f"首页性别匹配不一致(*>﹏<*)【{full_name[0]}】【{title}】")
                                self.callback_msg = "首页性别匹配不一致"
                                return False
                        else:
                            sex = "F"
                    
                    elif age_type == 1:
                        if "Mstr." == title or "Mstr." == title:
                            if "MSTR" == full_name[0]:
                                sex = "M"
                            else:
                                self.logger.info(f"首页性别匹配不一致(*>﹏<*)【{full_name[0]}】【{title}】")
                                self.callback_msg = "首页性别匹配不一致"
                                return False
                        else:
                            sex = "F"
                
                home_last = self.BPR.parse_to_clear(home_last)
                login_last = self.BPR.parse_to_clear(login_last)
                home_first = self.BPR.parse_to_separate(home_first)
                login_first = self.BPR.parse_to_separate(login_first)
                if home_last != login_last or home_first != login_first:
                    print(home_first, login_first)
                    self.logger.info(f"首页姓名匹配不一致(*>﹏<*)【{home_last}】【{login_last}】")
                    self.callback_msg = "首页姓名匹配不一致"
                    return False
                # # # 解析其他参数
                passport, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGUserList_ctl00__{i}>td:nth-child(5)", self.login_source)
                
                birthday, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGUserList_ctl00__{i}>td:nth-child(7)", self.login_source)
                birthday = self.DFR.format_to_transform(birthday, '%d-%b-%Y')
                birthday = birthday.strftime("%Y-%m-%d")
                
                nationality, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", f"#ctl00_bodycontent_RGUserList_ctl00__{i}>td:last-child", self.login_source)
                nationality = self.CMR.select_from_country(nationality)
                
                baggage = self.baggage.get(f"{login_last}/{login_first}", [])
                
                aux = []
                if baggage:
                    baggage = f"{baggage}KG"
                    aux = [{'departureAircode': '', 'arrivalAircode': '', 'tripType': 1, 'detail': baggage, 'productType': '1'}]
                
                self.passengers.append({
                    "passengerName": f"{login_last}/{login_first}", "passengerBirthday": birthday,
                    "passengerSex": sex, "passengerType": age_type, "passengerNationality": nationality,
                    "identificationNumber": passport, "cardType": "", "cardExpired": "",
                    "service_type": "", "auxArray": aux
                })
            
            return True
        self.logger.info("解析乘客失败(*>﹏<*)【detail】")
        self.callback_msg = "解析乘客失败"
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
