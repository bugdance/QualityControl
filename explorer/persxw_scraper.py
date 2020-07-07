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
from detector.persxw_simulator import PersXWSimulator


class PersXWScraper(RequestWorker):
    """XW采集器

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
        self.PSR = PersXWSimulator()  # TR模拟器
        # # # 请求中用到的变量
        self.ajax_header: str = ""  # 认证ajax header
        # # # 返回中用到的变量
        self.order_status: str = ""     # 订单状态
        self.segments: list = []        # 航段信息
        self.passengers: list = []      # 乘客信息
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
        self.PSR.logger = self.logger
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
        
        if self.process_to_index():
            if self.process_to_search():
                if self.process_to_segment():
                    if self.process_to_passenger():
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

    def process_to_ajax(self, js_url: str = "", referer_url: str = ""):
        """

        Args:
            js_url:

        Returns:

        """
        # # # 获取challenge
        self.RCR.url = "https://book.nokscoot.com" + js_url
        self.RCR.param_data = None
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        self.RCR.header.update({
            "Accept": "*/*",
            "Host": "book.nokscoot.com",
            "Referer": referer_url,
        })
        self.RCR.post_data = None
        if self.RCR.request_to_get():
            self.ajax_header, temp_list = self.BPR.parse_to_regex('ajax_header:"(.*?)",', self.RCR.page_source)
            url, temp_list = self.BPR.parse_to_regex('path:"(.*?)",', self.RCR.page_source)
            if self.ajax_header:
                # # # 获取challenge
                self.RCR.url = "https://book.nokscoot.com" + url
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "*/*",
                    "Content-Type": "text/plain;charset=UTF-8",
                    "Host": "book.nokscoot.com",
                    "Origin": "https://book.nokscoot.com",
                    "Referer": referer_url,
                    "X-Distil-Ajax": self.ajax_header
                })
            
                o = self.PSR.recognize_to_identify()
                ua = self.BPR.parse_to_clear(self.user_agent)
            
                data = '{"proof":"%s","cookies":1,"setTimeout":0,"setInterval":0,' \
                       '"appName":"Netscape","platform":"Win32","syslang":"zh-CN","userlang":"zh-CN","cpu":"",' \
                       '"productSub":"20030107","plugins":{"0":"ChromePDFPlugin","1":"ChromePDFViewer","2":' \
                       '"NativeClient"},"mimeTypes":{"0":"application/pdf","1":' \
                       '"PortableDocumentFormatapplication/x-google-chrome-pdf","2":' \
                       '"NativeClientExecutableapplication/x-nacl","3":' \
                       '"PortableNativeClientExecutableapplication/x-pnacl"},"screen":{"width":1920,"height":1080,' \
                       '"colorDepth":24},"fonts":{"0":"Calibri","1":"Cambria","2":"Times","3":"Constantia","4":' \
                       '"LucidaBright","5":"Georgia","6":"SegoeUI","7":"Candara","8":"TrebuchetMS","9":"Verdana",' \
                       '"10":"Consolas","11":"LucidaConsole","12":"LucidaSansTypewriter","13":"CourierNew","14":' \
                       '"Courier"},"fp2":{"userAgent":' \
                       '"%s","language":"zh-CN","screen":{"width":1920,"height":1080,"availHeight":1040,' \
                       '"availWidth":1920,"pixelDepth":24,"innerWidth":1259,"innerHeight":803,"outerWidth":1275,' \
                       '"outerHeight":891,"devicePixelRatio":1},"timezone":8,"indexedDb":true,"addBehavior":false,' \
                       '"openDatabase":true,"cpuClass":"unknown","platform":"Win32","doNotTrack":"unknown","plugins":' \
                       '"ChromePDFPlugin::PortableDocumentFormat::application/x-google-chrome-pdf~pdf;' \
                       'ChromePDFViewer::::application/pdf~pdf;NativeClient::::application/x-nacl~,' \
                       'application/x-pnacl~","canvas":{"winding":"yes","towebp":true,"blending":true,"img":' \
                       '"bee56b0a4dcf5bc3040ee3f938f6efd48ad5fd68"},"webGL":{"img":' \
                       '"bd6549c125f67b18985a8c509803f4b883ff810c","extensions":"ANGLE_instanced_arrays;' \
                       'EXT_blend_minmax;EXT_color_buffer_half_float;EXT_disjoint_timer_query;EXT_float_blend;' \
                       'EXT_frag_depth;EXT_shader_texture_lod;EXT_texture_filter_anisotropic;' \
                       'WEBKIT_EXT_texture_filter_anisotropic;EXT_sRGB;KHR_parallel_shader_compile;' \
                       'OES_element_index_uint;OES_standard_derivatives;OES_texture_float;' \
                       'OES_texture_float_linear;OES_texture_half_float;OES_texture_half_float_linear;' \
                       'OES_vertex_array_object;WEBGL_color_buffer_float;WEBGL_compressed_texture_s3tc;' \
                       'WEBKIT_WEBGL_compressed_texture_s3tc;WEBGL_compressed_texture_s3tc_srgb;' \
                       'WEBGL_debug_renderer_info;WEBGL_debug_shaders;WEBGL_depth_texture;' \
                       'WEBKIT_WEBGL_depth_texture;WEBGL_draw_buffers;WEBGL_lose_context;' \
                       'WEBKIT_WEBGL_lose_context","aliasedlinewidthrange":"[1,1]","aliasedpointsizerange":' \
                       '"[1,1024]","alphabits":8,"antialiasing":"yes","bluebits":8,"depthbits":24,"greenbits":8,' \
                       '"maxanisotropy":16,"maxcombinedtextureimageunits":32,"maxcubemaptexturesize":16384,' \
                       '"maxfragmentuniformvectors":1024,"maxrenderbuffersize":16384,"maxtextureimageunits":16,' \
                       '"maxtexturesize":16384,"maxvaryingvectors":30,"maxvertexattribs":16,' \
                       '"maxvertextextureimageunits":16,"maxvertexuniformvectors":4096,"maxviewportdims":' \
                       '"[32767,32767]","redbits":8,"renderer":"WebKitWebGL","shadinglanguageversion":' \
                       '"WebGLGLSLES1.0(OpenGLESGLSLES1.0Chromium)","stencilbits":0,"vendor":"WebKit","version":' \
                       '"WebGL1.0(OpenGLES2.0Chromium)","vertexshaderhighfloatprecision":23,' \
                       '"vertexshaderhighfloatprecisionrangeMin":127,"vertexshaderhighfloatprecisionrangeMax":127,' \
                       '"vertexshadermediumfloatprecision":23,"vertexshadermediumfloatprecisionrangeMin":127,' \
                       '"vertexshadermediumfloatprecisionrangeMax":127,"vertexshaderlowfloatprecision":23,' \
                       '"vertexshaderlowfloatprecisionrangeMin":127,"vertexshaderlowfloatprecisionrangeMax":127,' \
                       '"fragmentshaderhighfloatprecision":23,"fragmentshaderhighfloatprecisionrangeMin":127,' \
                       '"fragmentshaderhighfloatprecisionrangeMax":127,"fragmentshadermediumfloatprecision":23,' \
                       '"fragmentshadermediumfloatprecisionrangeMin":127,' \
                       '"fragmentshadermediumfloatprecisionrangeMax":127,"fragmentshaderlowfloatprecision":23,' \
                       '"fragmentshaderlowfloatprecisionrangeMin":127,"fragmentshaderlowfloatprecisionrangeMax":127,' \
                       '"vertexshaderhighintprecision":0,"vertexshaderhighintprecisionrangeMin":31,' \
                       '"vertexshaderhighintprecisionrangeMax":30,"vertexshadermediumintprecision":0,' \
                       '"vertexshadermediumintprecisionrangeMin":31,"vertexshadermediumintprecisionrangeMax":30,' \
                       '"vertexshaderlowintprecision":0,"vertexshaderlowintprecisionrangeMin":31,' \
                       '"vertexshaderlowintprecisionrangeMax":30,"fragmentshaderhighintprecision":0,' \
                       '"fragmentshaderhighintprecisionrangeMin":31,"fragmentshaderhighintprecisionrangeMax":30,' \
                       '"fragmentshadermediumintprecision":0,"fragmentshadermediumintprecisionrangeMin":31,' \
                       '"fragmentshadermediumintprecisionrangeMax":30,"fragmentshaderlowintprecision":0,' \
                       '"fragmentshaderlowintprecisionrangeMin":31,"fragmentshaderlowintprecisionrangeMax":30,' \
                       '"unmaskedvendor":"GoogleInc.","unmaskedrenderer":' \
                       '"ANGLE(Intel(R)HDGraphics630Direct3D11vs_5_0ps_5_0)"},"touch":{"maxTouchPoints":0,' \
                       '"touchEvent":false,"touchStart":false},"video":{"ogg":"probably","h264":"probably","webm":' \
                       '"probably"},"audio":{"ogg":"probably","mp3":"probably","wav":"probably","m4a":"maybe"},' \
                       '"vendor":"GoogleInc.","product":"Gecko","productSub":"20030107","browser":{"ie":false,' \
                       '"chrome":true,"webdriver":false},"window":{"historyLength":2,"hardwareConcurrency":8,' \
                       '"iframe":false,"battery":true},"location":{"protocol":"https:"},"fonts":"Calibri;' \
                       'Century;Haettenschweiler;Marlett;Pristina;SimHei","devices":{"count":3,"data":{"0":{' \
                       '"deviceId":"default","groupId":' \
                       '"5c2859e09d41b27c59de2b28837560cc25aafef9929f664e307e17fd2b1bd335","kind":"audiooutput",' \
                       '"label":""},"1":{"deviceId":"communications","groupId":' \
                       '"5c2859e09d41b27c59de2b28837560cc25aafef9929f664e307e17fd2b1bd335","kind":"audiooutput",' \
                       '"label":""},"2":{"deviceId":' \
                       '"2f2a091339475b73dadb679955354ff320b9aae108e009f7536f6cda8c761928","groupId":' \
                       '"5c2859e09d41b27c59de2b28837560cc25aafef9929f664e307e17fd2b1bd335","kind":' \
                       '"audiooutput","label":""}}}}}' % (o, ua)
            
                self.RCR.post_data = [
                    ("p", data)
                ]
                if self.RCR.request_to_post():
                    return True
        return False

    def set_cookies_acw_sc(self):
        arg1 = self.RCR.page_source[25:65]
        base = "3000176000856006061501533003690027800375"
        trans = ""
        res = ''
        try:
            list_1 = [0xf, 0x23, 0x1d, 0x18, 0x21, 0x10, 0x1, 0x26, 0xa, 0x9, 0x13, 0x1f, 0x28, 0x1b, 0x16,
                      0x17, 0x19, 0xd, 0x6, 0xb, 0x27, 0x12, 0x14, 0x8, 0xe, 0x15, 0x20, 0x1a, 0x2, 0x1e, 0x7,
                      0x4, 0x11, 0x5,
                      0x3, 0x1c, 0x22, 0x25, 0xc, 0x24]
            for i in range(len(list_1)):
                trans += arg1[list_1[i] - 1]
            for i in range(0, len(trans), 2):
                v1 = int(trans[i: i + 2], 16)
                v2 = int(base[i: i + 2], 16)
                res += "%02x" % (v1 ^ v2)
            self.RCR.set_to_cookies(False,
                cookie_list=[{"name": 'acw_sc_v2',
                              "value": res,
                              # 'domain': 'makeabooking.flyscoot.com',
                              # 'path': '/'
                              }]
            )
            return True
        except Exception as ex:
            self.callback_msg = f"设置 Cookie 失败 | {ex}"
            return False

    def process_to_verify(self, captcha_url: str = "", referer_url: str = "", js_url: str = "",
                          count: int = 0, max_count: int = 3) -> bool:
        """Verify process. 验证过程。

        Args:
            captcha_url
            referer_url
            js_url
            count (int): 累计计数。
            max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            if self.process_to_ajax(js_url, referer_url):
                # # # 获取challenge
                self.RCR.url = "https://book.nokscoot.com/distil_r_captcha_challenge"
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.header.update({
                    "Accept": "*/*",
                    "Host": "book.nokscoot.com",
                    "Origin": "https://book.nokscoot.com",
                    "Referer": referer_url,
                    "X-Distil-Ajax": self.ajax_header
                })
                self.RCR.post_data = None
                if self.RCR.request_to_post():
                    challenge, temp_list = self.BPR.parse_to_regex("(.*?);", self.RCR.page_source)
                    if challenge:
                        # # # 获取mp3地址
                        self.RCR.url = "http://api-na.geetest.com/get.php"
                        self.RCR.param_data = (
                            ("gt", "f2ae6cadcf7886856696502e1d55e00c"), ("challenge", challenge),
                            ("type", "voice"), ("lang", "zh-cn"), ("callback", ""),
                        )
                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                        self.RCR.header.update({
                            "Accept": "*/*",
                            "Host": "api-na.geetest.com",
                            "Referer": referer_url
                        })
                        if self.RCR.request_to_get():
                            get_json = self.RCR.page_source.strip("()")
                            get_json = self.BPR.parse_to_dict(get_json)
                            voice_path, temp_list = self.BPR.parse_to_path("$.data.new_voice_path", get_json)
                            voice_path, temp_list = self.BPR.parse_to_regex("/voice/zh/(.*).mp3", voice_path)
                            if not voice_path:
                                self.logger.info(f"认证音频地址错误(*>﹏<*)【{self.RCR.page_source}】")
                                self.callback_msg = "认证音频地址错误"
                                return self.process_to_verify(captcha_url, referer_url, js_url, count + 1, max_count)
                            else:
                                # # # 获取mp3文件
                                self.RCR.url = "http://114.55.207.125:50005/getcaptcha/geetest/" + voice_path
                                self.RCR.param_data = None
                                self.RCR.header = None
                                if self.RCR.request_to_get():
                                    # # 识别语音
                                    number, temp_list = self.BPR.parse_to_regex("\d+", self.RCR.page_source)
                                    if number:
                                        # # # 获取validate
                                        self.RCR.url = "http://api-na.geetest.com/ajax.php"
                                        self.RCR.param_data = (
                                            ("gt", "f2ae6cadcf7886856696502e1d55e00c"),
                                            ("challenge", challenge),
                                            ("a", number), ("lang", "zh-cn"), ("callback", "")
                                        )
                                        self.RCR.header = self.BFR.format_to_same(self.init_header)
                                        self.RCR.header.update({
                                            "Accept": "*/*",
                                            "Host": "api-na.geetest.com",
                                            "Referer": referer_url
                                        })
                                        if self.RCR.request_to_get():
                                            get_json = self.RCR.page_source.strip("()")
                                            get_json = self.BPR.parse_to_dict(get_json)
                                            validate, temp_list = self.BPR.parse_to_path("$.data.validate", get_json)
                                            if "url=" in captcha_url:
                                                cap_url, temp_list = self.BPR.parse_to_regex(
                                                    "url=(.*)", captcha_url)
                                            else:
                                                cap_url = captcha_url
                                            if not validate or not cap_url:
                                                self.logger.info(f"认证提交地址错误(*>﹏<*)【{self.RCR.page_source}】")
                                                self.callback_msg = "认证提交地址错误"
                                                return self.process_to_verify(
                                                    captcha_url, referer_url, js_url, count + 1, max_count)
                                            else:
                                                # # # 提交认证
                                                self.RCR.url = "https://book.nokscoot.com" + cap_url
                                                self.RCR.param_data = None
                                                self.RCR.header = self.BFR.format_to_same(self.init_header)
                                                self.RCR.header.update({
                                                    "Accept": "*/*",
                                                    "Content-Type": "application/x-www-form-urlencoded",
                                                    "Host": "book.nokscoot.com",
                                                    "Origin": "https://book.nokscoot.com",
                                                    "Referer": referer_url,
                                                    "X-Distil-Ajax": self.ajax_header
                                                })
                                                self.RCR.post_data = [
                                                    ("dCF_ticket", ""), ("geetest_challenge", challenge),
                                                    ("geetest_validate", validate),
                                                    ("geetest_seccode", f"{validate}|jordan"),
                                                    ("isAjax", "1"),
                                                ]
                                                if self.RCR.request_to_post(status_code=204):
                                                    self.logger.info("语音识别认证成功(*^__^*)【verify】")
                                                    return True
        
            self.logger.info(f"认证第{count + 1}次超时或者错误(*>﹏<*)【verify】")
            self.callback_msg = f"认证第{count + 1}次超时或者错误"
            return self.process_to_verify(captcha_url, referer_url, js_url, count + 1, max_count)
    
    def process_to_index(self, count: int = 0, max_count: int = 3):
        """Login process. 首页过程。

        Args:
        	count (int): 累计计数。
        	max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            self.RCR.url = "https://book.nokscoot.com/RetrieveBooking.aspx?nok=true&culture=en-SG"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Host": "book.nokscoot.com",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_index(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/RetrieveBooking.aspx?nok=true&culture=en-SG"):
                        return self.process_to_index(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url, "https://book.nokscoot.com/RetrieveBooking.aspx?nok=true&culture=en-SG"):
                        return self.process_to_index(count + 1, max_count)
        
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/RetrieveBooking.aspx?nok=true&culture=en-SG"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_index(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【index】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_index(count + 1, max_count)
                else:
                    self.logger.info("登录流程不走验证(*^__^*)【login】")
                    self.RCR.copy_source = self.BFR.format_to_same(self.RCR.page_source)
                    return True

            self.logger.info(f"首页第{count + 1}次超时或者错误(*>﹏<*)【index】")
            self.callback_msg = f"首页第{count + 1}次超时或者错误"
            return self.process_to_index(count + 1, max_count)
    
    def process_to_search(self, count: int = 0, max_count: int = 3) -> bool:
        """Login process. 首页过程。

        Args:
        	count (int): 累计计数。
        	max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            self.RCR.url = "https://book.nokscoot.com/RetrieveBooking.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Host": "book.nokscoot.com",
                "Origin": "https://book.nokscoot.com",
                "Referer": "https://book.nokscoot.com/RetrieveBooking.aspx?nok=true&culture=en-SG",
                "Upgrade-Insecure-Requests": "1"
            })
            param_batch = [
                ("__EVENTTARGET", False, "BookingRetrieveRetrieveBookingView$LinkButtonSubmit"),
                ("__EVENTARGUMENT", True, "#__EVENTARGUMENT"),
                ("__VIEWSTATE", True, "#__VIEWSTATE"),
                ("__XVIEWSTATEUSERKEY", True, "#__XVIEWSTATEUSERKEY"),
                ("pageToken", True, "input[name=pageToken]"),
                ("BookingRetrieveValidate.RecordLocator", False, self.CPR.record),
                ("BookingRetrieveValidate.ContactEmail", False, ""),
                ("BookingRetrieveValidate.PassengerFirstName", False, self.CPR.first_name),
                ("BookingRetrieveValidate.OriginStation", False, self.CPR.departure_code),
                ("BookingRetrieveValidate.PassengerLastName", False, self.CPR.last_name),
                ("BookingRetrieveValidate.DestinationStation", False, self.CPR.arrival_code),
            ]
            self.RCR.post_data = self.DPR.parse_to_batch("value", "css", param_batch, self.RCR.copy_source)
            if self.RCR.request_to_post(is_redirect=True):
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_search(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url,
                                            "https://book.nokscoot.com/RetrieveBooking.aspx"):
                        return self.process_to_search(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url,
                                            "https://book.nokscoot.com/RetrieveBooking.aspx"):
                        return self.process_to_search(count + 1, max_count)
    
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/RetrieveBooking.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_search(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【search】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_search(count + 1, max_count)
                else:
                    self.logger.info("搜索流程不走验证(*^__^*)【search】")
                    self.RCR.copy_source = self.BFR.format_to_same(self.RCR.page_source)
    
                    passenger, temp_list = self.DPR.parse_to_attributes(
                        "class", "css", ".ancillary-baggage.manageancillary-baggage", self.RCR.page_source)
                    if passenger:
                        return True
                    else:
                        self.logger.info("获取不到乘客按钮(*>﹏<*)【search】")
                        self.callback_msg = "获取不到乘客按钮，可能已经起飞"
                        return False
                    
            self.logger.info(f"搜索第{count + 1}次超时或者错误(*>﹏<*)【search】")
            self.callback_msg = f"搜索第{count + 1}次超时或者错误"
            return self.process_to_search(count + 1, max_count)
    
    def process_to_passenger(self, count: int = 0, max_count: int = 3) -> bool:
        """Login process. 首页过程。

        Args:
        	count (int): 累计计数。
        	max_count (int): 最大计数。

        Returns:
            bool
        """
        if count >= max_count:
            return False
        else:
            self.RCR.url = "https://book.nokscoot.com/ManagePassengers.aspx"
            self.RCR.param_data = None
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.header.update({
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Host": "book.nokscoot.com",
                "Referer": "https://book.nokscoot.com/ManageBooking.aspx",
                "Upgrade-Insecure-Requests": "1"
            })
            if self.RCR.request_to_get():
                # # # 查封禁
                if "acw_sc_v2" in self.RCR.page_source:
                    self.logger.info("有封禁")
                    self.set_cookies_acw_sc()
                    return self.process_to_passenger(count + 1, max_count)
                # # # 查Access Denied
                denied, temp_list = self.DPR.parse_to_attributes(
                    "text", "css", "h1", self.RCR.page_source)
                if "Access Denied" in denied:
                    self.logger.info("有拒绝")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url,
                                            "https://book.nokscoot.com/ManagePassengers.aspx"):
                        return self.process_to_passenger(count + 1, max_count)
                # # # 查block
                block, temp_list = self.DPR.parse_to_attributes(
                    "id", "css", "#distilIdentificationBlockPOST", self.RCR.page_source)
                if block:
                    self.logger.info("有block")
                    js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                    if self.process_to_ajax(js_url,
                                            "https://book.nokscoot.com/ManagePassengers.aspx"):
                        return self.process_to_passenger(count + 1, max_count)
    
                # # # 查询验证标签
                content_url, temp_list = self.DPR.parse_to_attributes(
                    "content", "css", "meta[http-equiv=refresh]", self.RCR.page_source)
                action_url, temp_list = self.DPR.parse_to_attributes(
                    "action", "css", "#distilCaptchaForm", self.RCR.page_source)
                js_url, temp_list = self.DPR.parse_to_attributes("src", "css", "script[src]", self.RCR.page_source)
                if content_url or action_url:
                    verify_url = "https://book.nokscoot.com/ManagePassengers.aspx"
                    if content_url:
                        captcha_url = content_url
                    else:
                        captcha_url = action_url
                    if js_url:
                        if self.process_to_verify(captcha_url, verify_url, js_url):
                            return self.process_to_passenger(count + 1, max_count)
                        else:
                            return False
                    else:
                        self.logger.info("获取认证地址错误(*>﹏<*)【passenger】")
                        self.callback_msg = "获取认证地址错误"
                        return self.process_to_passenger(count + 1, max_count)
                else:
                    self.logger.info("乘客流程不走验证(*^__^*)【passenger】")
                    return True
    
            self.logger.info(f"乘客第{count + 1}次超时或者错误(*>﹏<*)【passenger】")
            self.callback_msg = f"乘客第{count + 1}次超时或者错误"
            return self.process_to_passenger(count + 1, max_count)

    def process_to_segment(self) -> bool:
        """收集航段信息
        :return:  bool
        """
        self.order_status = "Confirmed"
        # # # 从详情页收集航段信息
        segments, segments_list = self.DPR.parse_to_attributes(
            "class", "css", "#left_content div.black_wrapper div.item_wrapper", self.RCR.page_source)
        if segments_list:
            for i in range(len(segments_list)):
                segments, code_list = self.DPR.parse_to_attributes(
                    "value", "xpath", f"//div[@id='left_content']//div[@class='black_wrapper']"
                    f"//div[@class='item_wrapper'][{i+1}]/text()", self.RCR.page_source)
                from_code = self.BPR.parse_to_clear(code_list[1])
                to_code = self.BPR.parse_to_clear(code_list[2])
                
                flight_num, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath", f"//div[@class='itinerary_detail_box']"
                    f"//div[@class='itinerary_detail_time'][{i+1}]//div[@class='itinerary_detail_number']/text()", self.RCR.page_source)
                flight_num = self.BPR.parse_to_clear(flight_num)
                from_date, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath", f"//div[@id='left_content']//div[@class='black_wrapper']"
                    f"//div[@class='item_wrapper'][{i+1}]//strong/text()", self.RCR.page_source)
                from_date = self.BPR.parse_to_clear(from_date)

                departure_code, temp_list = self.BPR.parse_to_regex("(.*)-", from_code)
                arrival_code, temp_list = self.BPR.parse_to_regex("(.*)-", to_code)

                from_time, temp_list = self.BPR.parse_to_regex("-(.*)", from_code)
                from_time = self.DFR.format_to_transform(from_time, "%H:%M")
                to_time, temp_list = self.BPR.parse_to_regex("-(.*)", to_code)
                to_time = self.DFR.format_to_transform(to_time, "%H:%M")
        
                if to_time.hour < from_time.hour:
                    to_date = self.DFR.format_to_transform(from_date, "%d%b%Y")
                    to_date = self.DFR.format_to_custom(to_date, 1)
                    from_date = self.DFR.format_to_transform(from_date, "%d%b%Y")
                else:
                    to_date = self.DFR.format_to_transform(from_date, "%d%b%Y")
                    from_date = self.DFR.format_to_transform(from_date, "%d%b%Y")
                
                from_date = from_date.strftime("%Y%m%d")
                to_date = to_date.strftime("%Y%m%d")
                from_time = from_time.strftime("%H%M")
                to_time = to_time.strftime("%H%M")

                self.segments.append({
                    "departureAircode": departure_code, "arrivalAircode": arrival_code,
                    "flightNum": flight_num, "departureTime": from_date + from_time,
                    "arrivalTime": to_date + to_time, "tripType": i+1
                })
            return True
    
        self.logger.info("航段超时或者错误(*>﹏<*)【segments】")
        self.callback_msg = "航段超时或者错误"
        return False

    def process_to_detail(self) -> bool:
        """收集乘客信息
        :return:  bool
        """
        # # # 从详情页收集乘客信息
        passengers, passengers_list = self.DPR.parse_to_attributes(
            "class", "css", "div[class*='passenger_wrapper_cell']", self.RCR.page_source)
        if passengers_list:
            for i in range(len(passengers_list)):
                age_type = 0
                sex = "M"
                passenger, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath",
                    f"(//div[contains(@class, 'passenger_wrapper_cell')])[{i+1}]//table[contains(@class, 'namechange-display')]"
                    f"//input[@class='blocked pax_dob']/@data-passenger_type",
                    self.RCR.page_source)
                passenger = self.BPR.parse_to_separate(passenger)
                title, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath",
                    f"(//div[contains(@class, 'passenger_wrapper_cell')])[{i+1}]//table[contains(@class, 'namechange-display')]"
                    f"//input[@class='title blocked']/@value",
                    self.RCR.page_source)
                if "CHD" in passenger:
                    age_type = 1
                    if "Master" != title:
                        sex = "F"
                else:
                    if "Mr" != title:
                        sex = "F"

                first_name, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath",
                    f"(//div[contains(@class, 'passenger_wrapper_cell')])[{i+1}]//table[contains(@class, 'namechange-display')]"
                    f"//input[@class='first_name blocked']/@value",
                    self.RCR.page_source)
                last_name, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath",
                    f"(//div[contains(@class, 'passenger_wrapper_cell')])[{i+1}]//table[contains(@class, 'namechange-display')]"
                    f"//input[@class='last_name blocked']/@value",
                    self.RCR.page_source)

                birthday, temp_list = self.DPR.parse_to_attributes(
                    "value", "xpath",
                    f"(//div[contains(@class, 'passenger_wrapper_cell')])[{i+1}]//table[contains(@class, 'namechange-display')]"
                    f"//input[@class='blocked pax_dob']/@value",
                    self.RCR.page_source)
                birthday = self.BPR.parse_to_clear(birthday)
                birthday = self.DFR.format_to_transform(birthday, "%d%b,%Y")
                birthday = birthday.strftime("%Y-%m-%d")

                baggage = []
                aux, aux_list = self.DPR.parse_to_attributes(
                    "value", "xpath",
                    f"(//div[contains(@class, 'passenger_wrapper_cell')])[{i+1}]//div[@class='passenger_item_selectlist']/@class",
                    self.RCR.page_source)
                if aux_list:
                    for j in range(len(aux_list)):
                        weight, temp_list = self.DPR.parse_to_attributes(
                            "value", "xpath",
                            f"(//div[contains(@class, 'passenger_wrapper_cell')])[{i+1}]"
                            f"//div[@class='passenger_item_selectlist'][{j+1}]/div[@class='passenger_item_con_select']"
                            f"//input[@class='selected-baggage']/@value",
                            self.RCR.page_source)
                        if weight:
                            weight, temp_list = self.BPR.parse_to_regex("\d+", weight)
                            weight += "KG"
                            baggage.append({"departureAircode": "", "arrivalAircode": "", "tripType": j+1, "detail": weight, "productType": "1"})

                self.passengers.append({
                    "passengerName": f"{last_name}/{first_name}", "passengerBirthday": birthday,
                    "passengerSex": sex, "passengerType": age_type, "passengerNationality": "",
                    "identificationNumber": "", "cardType": "", "cardExpired": "",
                    "service_type": "", "auxArray": baggage
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

