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
from jwt.jwk import OctetJWK
from jwt import JWT
import random
import time


class Appn5JScraper(RequestWorker):
    """5JAPP采集器，个人账户质检
    """

    def __init__(self):
        RequestWorker.__init__(self)
        self.RCR = RequestCrawler()  # 请求爬行器。
        self.AFR = AESFormatter()    # AES格式器。
        self.BFR = BasicFormatter()  # 基础格式器。
        self.BPR = BasicParser()     # 基础解析器。
        self.CFR = CallBackFormatter()  # 回调格式器。
        self.CPR = CallInParser(False)  # 接入解析器。
        self.DFR = DateFormatter()   # 日期格式器。
        self.DPR = DomParser()       # 文档解析器。
        # # # 请求中用到的变量
        self.verify_token: str = ""  # 认证token
        # # # 返回中用到的变量
        self.order_status: str = ""  # 订单状态
        self.segments: list = []     # 航段信息
        self.passengers: list = []   # 乘客信息

        self.temp_source: str = ""   # 临时源数据

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
        self.RCR.timeout = 20  # 超时时间



        if self.get_proxy():
            # # 质检流程
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

    def get_proxy(self, count: int = 0, max_count: int = 4):
        """
        判断代理，在规定时间段内使用
        :return:
        """
        if count >= max_count:
            return False
        else:
            # 判断当前时间是否在 00:00 - 05:30 时间段， 如果符合则使用代理，否则不使用
            current_time = self.DFR.format_to_now()
            now = time.strptime(current_time.strftime('%H%M'), "%H%M")  # 当前时间
            if time.strptime('0000', "%H%M") < now < time.strptime('2330', "%H%M"):


                self.RCR.set_to_proxy(False, "")
                # 获取代理， 并配置代理
                # 托马斯
                # log_account = account[random.randint(0, len(account) - 1)]
                service_type = ["3", "4", "112"]
                self.RCR.url = 'http://cloudmonitorproxy.51kongtie.com/Proxy/getProxyByServiceType?proxyNum=1&serviceType=' + \
                               service_type[random.randint(0, 2)]
                # 塔台
                # self.RCR.url = 'http://cloudmonitorproxy.51kongtie.com/Proxy/getProxyByServiceType?proxyNum=1&serviceType=112'
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.param_data = None
                if self.RCR.request_to_get('json'):
                    for ip in self.RCR.page_source:
                        if ip.get('proxyIP'):
                            self.proxys = "http://yunku:123@" + str(ip.get('proxyIP')) + ":" + str(ip.get('prot'))
                            # self.proxys = "http://yunku:123@" + "60.179.17.209" + ":" + "3138"
                            # self.proxys = "http://94.249.236.165:8080"
                            self.RCR.set_to_proxy(enable_proxy=True, address=self.proxys)
                            return True
                        else:
                            self.callback_msg = f"代理地址获取失败"
                            self.logger.info(self.callback_msg)
                            return self.get_proxy(count + 1, max_count)
                else:
                    # self.RCR.set_to_proxy(enable_proxy=True, address='http://yunku:123@120.5.51.17:3138')
                    self.callback_msg = f"代理地址获取失败"
                    self.logger.info(self.callback_msg)
                    return self.get_proxy(count + 1, max_count)
            # return True
            else:
                # self.RCR.set_to_proxy(enable_proxy=True, address='http://yunku:123@120.5.51.17:3138')
                self.callback_msg = f"代理超出使用时间段【当前时间：{current_time}】"
                # 1, False 超出使用时间不跑。
                # 2, True  超出使用时间继续跑, 不使用代理。
                return False

    def process_to_index(self, count: int = 0, max_count: int = 4) -> bool:
        """首页查询航班流程
        :param count:  重试次数
        :param max_count:  重试最大次数
        :return:  bool
        """
        self.RCR.url = "https://mobile-api.cebupacificair.com/dotrez-prod-v3/api/v1/Token"
        self.RCR.param_data = None
        self.RCR.post_data = {"credentials":{"location":"MOB"},"applicationName":"cebumobileapp"}
        self.RCR.header = self.BFR.format_to_same(self.init_header)
        secret = self.create_jwt('', self.RCR.url)
        self.RCR.header.update({
            'Accept': '*/*',
            'Content-Type': 'application/json',
            "Host": "mobile-api.cebupacificair.com",
            'User-Agent': 'okhttp/3.12.3',
            'Accept-Encoding': 'gzip, deflate',
            'ocp-apim-subscription-key': '07ce68d9937841a59a8156ec7dafc0b6',
            'Authorization-Secret': secret
        })
        del self.RCR.header["Accept-Language"]
        if self.RCR.request_to_post(is_redirect=True, data_type="json", page_type='json', status_code=201):
            self.token = self.RCR.page_source.get('data').get('token')
            return True

        self.logger.info("首页超时或者错误(*>﹏<*)【home】")
        self.callback_msg = "首页超时或者错误"
        if count >= max_count:
            return False
        else:
            if self.get_proxy():
                return self.process_to_index(count + 1, max_count)
            else:
                return False

    def process_to_search(self, count: int = 0, max_count: int = 4) -> bool:
        """查询详情信息流程
        :param count:  重试次数
        :param max_count:  重试最大次数
        :return:  bool
        """
        if count >= max_count:
            return False
        else:
            # 判断接口账户是否符合要求, 如果不符合要求, 随机登陆账号, 否则直接使用接口提供的账号
            # 如果接口传的账号为空，没有@符号，包含qq.com, 包含163.com，则走自己账号
            if self.CPR.username == "" or "@" not in self.CPR.username or self.CPR.password == "" or \
                    "qq.com" in self.CPR.username or "163.com" in self.CPR.username:
                account = [
                    #{"username": 'olncptrjzpar@xuyangloveeat.ga', "password": '7232wslo$WLCS'},
                    #{"username": 'pzszzdfvcwra@xuyangloveeat.ga', "password": '0029inhj$NOEO'},
                    {"username": 'mpwhxwyurhzl@xuyangloveeat.ga', "password": '0845skwx$PZDT'},
                    {"username": 'lwopqpfdiuzh@xuyangloveeat.ga', "password": '8601iruf$AFLF'},
                    #{"username": 'ombvemkxopri@xuyangloveeat.ga', "password": '3207dozb$VPIZ'},
                    #{"username": 'sbeufugaskhw@xuyangloveeat.ga', "password": '1101gjhx$WCZK'},
                    #{"username": 'zssufmbjpwni@xuyangloveeat.ga', "password": '3015iscx$LDZU'},
                    #{"username": 'mqxswkntcbue@xuyangloveeat.ga', "password": '5887wcvf$TMFJ'},
                    {"username": 'xmzhurvwxtrm@xuyangloveeat.ga', "password": '7392cdjj$ZQOO'},
                    {"username": 'sheshou1111@126.com', "password": 'Pa$sw0rd71'},
                    {"username": 'sheshou6666@126.com', "password": 'Pa$sw0rd71'},
                    {"username": 'shehsou5555@126.com', "password": 'Pa$sw0rd71'},
                    {"username": 'sheshou0000@126.com', "password": 'Pa$sw0rd71'},
                    {"username": 'qicaisheshou4@126.com', "password": 'Pa$sw0rd71'},
                ]
                log_account = account[random.randint(0, len(account) - 1)]
                self.CPR.username = log_account.get('username')
                self.CPR.password = log_account.get('password')

            self.logger.info(f"登陆账号: {self.CPR.username}")
            self.RCR.url = "https://mobile-api.cebupacificair.com/dotrez-prod-v3/api/nsk/v1/Token"
            self.RCR.header = self.BFR.format_to_same(self.init_header)
            self.RCR.post_data = '{"Credentials":{"Username":"' + self.CPR.username + '","Password":"' + self.CPR.password + '","Domain":"WWW","Location":"MOB"},"ApplicationName":"cebumobileapp"}'
            secret = self.create_jwt(self.token, self.RCR.url)
            self.RCR.header.update({
                'Accept': 'application/json',
                'ocp-apim-subscription-key': '07ce68d9937841a59a8156ec7dafc0b6',
                'Content-Type': 'application/json',
                "Host": "mobile-api.cebupacificair.com",
                'User-Agent': 'okhttp/3.12.3',
                'Accept-Encoding': 'gzip, deflate',
                'Authorization': self.token,
                'Authorization-Secret': secret,
            })
            del self.RCR.header["Accept-Language"]
            if self.RCR.request_to_post(is_redirect=True, page_type='json', status_code=201):
                errors = self.RCR.page_source.get('errors')
                if errors:
                    self.callback_msg = f"登陆失败 | 账户: {self.CPR.username}"
                    self.logger.info(f"登陆失败 | 账户: {self.CPR.username} | 密码{self.CPR.password} | {errors}")
                    return False

                if "data" in self.RCR.page_source:
                    self.token = self.RCR.page_source.get('data').get('token')
                else:
                    self.callback_msg = f"登陆失败 | 账户: {self.CPR.username}"
                    self.logger.info(f"登陆失败 | 账户: {self.CPR.username} | 密码{self.CPR.password}")
                    return False

                # # # 获取用户信息
                self.RCR.url = "https://mobile-api.cebupacificair.com/dotrez-prod-v3/custom/v3/user/bookings"
                self.RCR.post_data = None
                self.RCR.param_data = None
                self.RCR.header = self.BFR.format_to_same(self.init_header)

                secret = self.create_jwt(self.token, self.RCR.url)
                self.RCR.header.update({
                    'ocp-apim-subscription-key': '07ce68d9937841a59a8156ec7dafc0b6',
                    'Authorization': self.token,
                    'Authorization-Secret': secret,
                    "Host": "mobile-api.cebupacificair.com",
                    'User-Agent': 'okhttp/3.12.3',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                })
                del self.RCR.header["Accept-Language"]
                if not self.RCR.request_to_get(is_redirect=True, page_type='json'):
                    self.callback_msg = f"获取用户信息失败 [user/bookings]"
                    self.logger.info(self.callback_msg)
                    return False

                self.RCR.url = "https://mobile-api.cebupacificair.com/dotrez-prod-v3/api/v1/Graph"
                self.RCR.header = self.BFR.format_to_same(self.init_header)
                self.RCR.post_data = '''{"Query":" query memberBooking0 { bookings(request: { recordLocator: \\"''' + self.CPR.record + '''\\", firstName: \\"''' + self.BPR.parse_to_separate(
                    self.CPR.first_name) + '''\\", lastName: \\"''' + self.BPR.parse_to_separate(
                    self.CPR.last_name) + '''\\"}) { ...Booking } }  fragment Name on Name { first last middle suffix title } fragment ServiceCharge on ServiceCharge { amount code collectType currencyCode detail foreignAmount foreignCurrencyCode ticketCode type } fragment Booking on Booking { bookingKey recordLocator currencyCode systemCode groupName locators { ...BookingRecordLocators } info { ...BookingInfo } typeOfSale { ...TypeOfSale } hold { ...BookingHold } breakdown { ...BookingBreakDown } contacts { ...KeyValuePair_NonNullGraphTypeStringGraphType_Contact } passengers { ...KeyValuePair_StringGraphType_Passenger } journeys { ...Journey } comments { ...BookingComment } queues { ...BookingQueueInfo } history { ...BookingHistory } payments { ...Payment } addOns { ...KeyValuePair_StringGraphType_AddOn } } fragment KeyValuePair_StringGraphType_Passenger on KeyValuePair_StringGraphType_Passenger { value { ...Passenger } } fragment Contact on Contact { contactTypeCode cultureCode emailAddress customerNumber sourceOrganization distributionOption notificationPreference name { ...Name } } fragment KeyValuePair_StringGraphType_AddOn on KeyValuePair_StringGraphType_AddOn { value { ...AddOn } } fragment AddOn on AddOn { paymentRequired addOnKey type summary { ...AddOnOrderSummary } reference created { ...CreatedAddOnDetails } source { ...AddOnDetails } declinedText cultureCode modifiedDate modifiedAgentReference order { ...Order } isHistorical charges { ...AddOnCharge } } fragment AddOnDetails on AddOnDetails { agentCode domainCode locationCode organizationCode } fragment KeyValuePair_NonNullGraphTypeStringGraphType_Contact on KeyValuePair_NonNullGraphTypeStringGraphType_Contact { value { ...Contact } } fragment AddOnCharge on AddOnCharge { type code ticketCode collection currencyCode amount details } fragment OrderPriceBreakdown on OrderPriceBreakdown { display { ...Amount } initial { ...Amount } markup { ...Amount } listed { ...Amount } listedDiscount { ...Amount } discount { ...Amount } handling { ...Amount } handlingDiscount { ...Amount } dueNow { ...AmountDue } dueLater { ...AmountDue } personalizations taxable services fees total taxRate taxExempt taxAtUnitPrice } fragment Amount on Amount { value total } fragment AmountDue on AmountDue { preTax tax total } fragment Order on Order { orderKey active locations { ...OrderLocation } criteria { ...OrderCriteria } customer { ...OrderCustomer } participants { ...KeyValuePair_StringGraphType_OrderParticipant } quantity history { ...OrderHistory } usageDate payment { ...OrderPayment } externalLocator description descriptionFormatType productDescription productVariationDescription paymentAction amounts { ...OrderPriceBreakdown } terms { ...Term } cancellationTerms { ...Term } fees { ...OrderFee } } fragment KeyValuePair_StringGraphType_OrderParticipant on KeyValuePair_StringGraphType_OrderParticipant { value { ...OrderParticipant } } fragment OrderParticipant on OrderParticipant { participantKey description name { ...Name } participantTypeCode isPrimary document { ...ParticipantDocument } emailAddress type } fragment OrderFee on OrderFee { code feeCategoryCode description amount { ...Amount } foreignAmount { ...Amount } type isWaiveable foreignCurrencyCode currencyCode } fragment Term on Term { code description terms } fragment OrderPayment on OrderPayment { paymentKey type currencyCode name { ...Name } expiration cvv amount description issueNumber emailAddress } fragment OrderHistory on OrderHistory { code previousCode note created hasError } fragment ParticipantDocument on ParticipantDocument { number issuedByCode documentTypeCode } fragment OrderCustomer on OrderCustomer { customerKey name { ...Name } customerNumber emailAddress type } fragment OrderCriteria on OrderCriteria { catalogCode countryCode supplierCode departmentCode vendorCode companyCode ratingCode discountCode promotionCode currencyCode categoryCode } fragment OrderLocation on OrderLocation { description code utcOffset usageDate } fragment CreatedAddOnDetails on CreatedAddOnDetails { agentReference agentCode date organizationCode domainCode locationCode } fragment AddOnOrderSummary on AddOnOrderSummary { total held charged supplierCode beginDate beginLocation endDate endLocation externalReference description } fragment Payment on Payment { paymentKey code approvalDate authorizationCode authorizationStatus fundedDate transactionCode createdDate modifiedDate type status transferred channelType deposit accountId addedToState createdAgentId modifiedAgentId details { ...PaymentDetails } amounts { ...PaymentAmounts }  attachments { ...PaymentAttachment } pointOfSale { agentCode domainCode locationCode organizationCode } voucher { ...PaymentVoucherDetails } } fragment PaymentVoucherDetails on PaymentVoucherDetails { id transactionId overrideRestrictions overrideAmount recordLocator } fragment PaymentAttachment on PaymentAttachment { id paymentId attachment } fragment PaymentAmounts on PaymentAmounts { amount currencyCode collected collectedCurrencyCode quoted quotedCurrencyCode } fragment PaymentDetails on PaymentDetails { accountNumberId parentPaymentId accountName accountNumber expirationDate text installments binRange fields { key value } } fragment BookingComment on BookingComment { type text createdDate } fragment BookingQueueInfo on BookingQueueInfo { segmentKey code subCode name queueId passengerId watchListId note type action mode } fragment BookingHistory on BookingHistory { receivedBy receivedByReference createdDate } fragment BookingRecordLocators on BookingRecordLocators { numericRecordLocator parentRecordLocator parentId } fragment BookingInfo on BookingInfo { status paidStatus priceStatus profileStatus bookingType channelType bookedDate createdDate expirationDate modifiedDate modifiedAgentId createdAgentId owningCarrierCode changeAllowed } fragment TypeOfSale on TypeOfSale { residentCountry promotionCode } fragment BookingHold on BookingHold { expiration } fragment BookingBreakDown on BookingPriceBreakdown { balanceDue pointsBalanceDue authorizedBalanceDue totalAmount totalPoints totalToCollect totalPointsToCollect totalCharged } fragment Passenger on Passenger { passengerKey infant { ...PassengerInfant } customerNumber name { ...Name } passengerTypeCode discountCode travelDocuments { ...PassengerTravelDocument } fees { ...PassengerFee } name { ...Name } bags { ...PassengerBag } program { ...PassengerProgram } info { ...PassengerInfo } } fragment PassengerTravelDocument on PassengerTravelDocument { birthCountry expirationDate issuedByCode issuedDate passengerTravelDocumentKey name { ...Name } nationality number documentTypeCode } fragment PassengerInfant on PassengerInfant { dateOfBirth gender name { ...Name } nationality residentCountry fees { ...InfantFee } } fragment InfantFee on InfantFee { code detail passengerFeeKey override flightReference createdDate isProtected serviceCharges { ...ServiceCharge } } fragment PassengerFee on PassengerFee { type ssrCode code ssrNumber detail paymentNumber passengerFeeKey override flightReference createdDate isProtected serviceCharges { ...ServiceCharge } } fragment PassengerBag on PassengerBag { identifier baggageKey nonStandard type osTag osTagDate taggedToStation stationCode weight taggedToCarrierCode weightType } fragment PassengerProgram on PassengerProgram { code levelCode number } fragment PassengerInfo on PassengerInformation { nationality residentCountry gender dateOfBirth familyNumber } fragment Journey on Journey { flightType stops journeyKey notForGeneralUser move { ...JourneyMove } designator { ...TransportationDesignator } segments { ...Segment } } fragment JourneyMove on JourneyMove { maxMoveBackDays maxMoveOutDays } fragment Segment on Segment { segmentKey designator { ...TransportationDesignator } fares { ...Fare } identifier { ...TransportationIdentifier } externalIdentifier { ...TransportationIdentifier } cabinOfService segmentType isStandby isBlocked isConfirming isHosted isChangeOfGauge changeReasonCode channelType international priorityCode salesDate passengerSegment { ...KeyValuePair_StringGraphType_PassengerSegment } legs { ...Leg } } fragment KeyValuePair_StringGraphType_PassengerSegment on KeyValuePair_StringGraphType_PassengerSegment { value { ...PassengerSegment } } fragment Leg on Leg { legKey designator { ...TransportationDesignator } operationsInfo { ...OperationsInformation } legInfo { ...LegInformation } nests { ...LegNest } } fragment LegNest on LegNest { adjustedCapacity classNest lid travelClassCode nestType legClasses { ...LegClass } } fragment LegClass on LegClass { classAllotted classAuthorizedUnits classNest classOfService classRank classSold classType cnxSold latestAdvancedReservation status thruSold } fragment LegInformation on LegInformation { departureTimeUtc arrivalTimeUtc adjustedCapacity arrivalTerminal arrivalTimeVariant backMoveDays capacity changeOfDirection codeShareIndicator departureTerminal departureTimeVariant equipmentType equipmentTypeSuffix eTicket irop lid marketingCode marketingOverride onTime operatedByText operatingCarrier operatingOpSuffix outMoveDays arrivalTime departureTime prbcCode scheduleServiceType sold status subjectToGovtApproval } fragment OperationsInformation on OperationsInformation { actualOffBlockTime actualOnBlockTime actualTouchDownTime airborneTime arrivalGate {...GateInformation} arrivalNote arrivalStatus baggageClaim departureGate {...GateInformation} departureNote departureStatus estimatedArrivalTime standardArrivalTime tailNumber departureTimes { ...DepartureEvent } } fragment DepartureEvent on DepartureEvent {estimated scheduled} fragment GateInformation on GateInformation{ actualGate estimatedGate} fragment PassengerSegment on PassengerSegment { passengerKey activityDate baggageAllowanceUsed baggageAllowanceWeight baggageAllowanceWeightType boardingSequence createdDate liftStatus modifiedDate overBookIndicator priorityDate timeChanged verifiedTravelDocs seats { ...PassengerSeat } ssrs { ...PassengerSsr } tickets { ...Ticket } bags { ...PassengerSegmentBag } scores { ...PassengerScore } boardingPassDetail { ...PassengerBoardingPassDetail } hasInfant seatPreferences { ...SeatPreferences } } fragment SeatPreferences on SeatPreferences { seat travelClass } fragment PassengerBoardingPassDetail on PassengerBoardingPassDetail { gateInformation priorityInformation cabinClass compartmentLevel boardingZone seatAssignment sequenceNumber } fragment PassengerScore on PassengerScore { guestValueCode score passengerKey } fragment PassengerSegmentBag on PassengerSegmentBag { baggageKey passengerKey arrivalStation status departureStation osTag } fragment Ticket on Ticket { ticketNumber infantTicketNumber ticketIndicator ticketStatus passengerKey } fragment PassengerSsr on PassengerSsr { ssrDuration ssrKey count ssrCode feeCode passengerKey ssrDetail ssrNumber market { ...MarketInformation } } fragment MarketInformation on MarketInformation { identifier { ...TransportationIdentifier } destination origin departureDate } fragment PassengerSeat on PassengerSeat { compartmentDesignator penalty unitDesignator arrivalStation departureStation passengerKey unitKey seatInformation { ...SeatInfo } } fragment SeatInfo on SeatInfo { deck seatSet } fragment TransportationDesignator on TransportationDesignator { destination origin arrival departure } fragment Fare on Fare { isGoverning downgradeAvailable fareKey carrierCode classOfService classType fareApplicationType fareBasisCode fareClassOfService fareSequence fareStatus inboundOutBound isAllotmentMarketFare originalClassOfService productClass ruleNumber ruleTariff travelClassCode crossReferenceClassOfService passengerFares { ...PassengerFare } } fragment PassengerFare on PassengerFare { fareDiscountCode discountCode passengerType serviceCharges { ...ServiceCharge } } fragment TransportationIdentifier on TransportationIdentifier { identifier carrierCode opSuffix } ","Variables":""}'''
                # self.logger.info(self.RCR.post_data)
                secret = self.create_jwt(self.token, self.RCR.url)
                self.RCR.header.update({
                    'Authorization': self.token,
                    'Authorization-Secret': secret,
                    'ocp-apim-subscription-key': '07ce68d9937841a59a8156ec7dafc0b6',
                    'Content-Type': 'application/json',
                    "Host": "mobile-api.cebupacificair.com",
                    'User-Agent': 'okhttp/3.12.3',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br',
                })
                del self.RCR.header["Accept-Language"]
                if not self.RCR.request_to_post(page_type='json'):  # 进行查询
                    self.callback_msg = f"获取航班信息失败"
                    self.logger.info(self.callback_msg)
                    if self.get_proxy():
                        return self.process_to_search(count + 1, max_count)
                    else:
                        return False

                error, temp_list = self.BPR.parse_to_path('$.errors', self.RCR.page_source)
                if error:
                    self.logger.info(f"查询订单有误 {error[0].get('message')} | process_to_search")
                    self.callback_msg = f"查询订单失败"
                    return False
                return True

            self.logger.info("详情超时或者错误(*>﹏<*)【detail】")
            self.callback_msg = "详情超时或者错误"
            if self.get_proxy():
                return self.process_to_search(count + 1, max_count)
            else:
                return False

    def process_to_segment(self, count: int = 0, max_count: int = 3) -> bool:
        """收集航段信息
        :return:  bool
        """
        # # # 获取订单状态
        self.order_status, temp_list = self.BPR.parse_to_path('$...status', self.RCR.page_source)
        self.paidStatus, temp_list = self.BPR.parse_to_path('$...paidStatus', self.RCR.page_source)
        if self.order_status != "Confirmed":
            self.callback_msg = f"订单状态有误 |状态: {self.order_status}"
            self.logger.info(f"订单状态有误 |订单状态: {self.order_status}")
            return False
        if self.paidStatus != "PaidInFull":
            self.callback_msg = f"订单状态 {self.order_status} |订单可能存在支付异常: {self.paidStatus}"
            self.logger.info(f"订单状态 {self.order_status} |订单可能存在支付异常: {self.paidStatus}")
            return False

        # 判断航班是否有变化
        queues, temp_list = self.BPR.parse_to_path('$..queues', self.RCR.page_source)
        changes = ["Cancelled Flight", "ScheduleTimeChange", "REFUND", "CANCEL", "CHANGE" ]    # 错误的
        if queues:
            for i in queues:
                for key, value in i.items():
                    if type(value) is str:
                        for c in changes:
                            if c.lower() in value.lower():
                                self.callback_msg = f"航班有问题:  {value}"
                                self.logger.info(f"{self.callback_msg} | {key}: {value} ")
                                return False

                    else:
                        continue

        segments, temp_list = self.BPR.parse_to_path('$...journeys', self.RCR.page_source)
        tripType = 1
        if segments:
            for index, segments in enumerate(segments):
                tripType += index
                for i in segments.get('segments'):
                    designator = i.get("designator")
                    identifier = i.get('identifier')

                    to_date = self.DFR.format_to_transform(designator.get('arrival'), '%Y-%m-%dT%H:%M:%S')
                    to_date = to_date.strftime("%Y%m%d%H%M")
                    from_date = self.DFR.format_to_transform(designator.get('departure'), '%Y-%m-%dT%H:%M:%S')
                    from_date = from_date.strftime("%Y%m%d%H%M")

                    self.segments.append({
                        "departureAircode": designator.get('origin'),
                        "arrivalAircode": designator.get('destination'),
                        "flightNum": identifier.get("carrierCode") + identifier.get('identifier'),
                        "departureTime": from_date,
                        "arrivalTime": to_date,
                        "tripType": tripType
                    })

            return True

        self.logger.info(f"获取航段信息失败 {temp_list}")
        self.callback_msg = f"获取航段信息失败"
        return False

    def process_to_detail(self, count: int = 0, max_count: int = 3) -> bool:
        """收集乘客信息
        :return:  bool
        """
        # # # # 从详情页收集乘客信息
        passengers, passengers_list = self.BPR.parse_to_path('$...passengers', self.RCR.page_source)
        if passengers_list:
            for i in passengers:
                # self.logger.info(i)
                info = i.get('value').get('name')
                first_name = info.get('first')
                last_name = info.get('last')

                sex = "M"
                age_type = 1
                # 性别 M：男性 F：女性
                if info.get('title') == "MS":
                    sex = "F"
                elif info.get('title') == "MR":
                    sex = "M"
                elif info.get('title') == "MISS":
                    sex = "F"
                else:
                    sex = "M"

                appreciation = []
                for bag in i.get('value').get('fees'):
                    if "BAG" in bag.get('code'):
                        for segment in self.segments:
                            if segment.get('flightNum') in  bag.get('flightReference') or \
                                    segment.get('departureAircode') + segment.get('arrivalAircode') in  bag.get('flightReference'):
                                appreciation.append({
                                    "productType": "1",   # 行李是 1
                                    "departureAircode": segment.get('departureAircode'),
                                    "arrivalAircode": segment.get('arrivalAircode'),
                                    "tripType": segment.get('tripType'),
                                    "detail":bag.get('code').replace("BAG", "") + "KG"
                                })
                        # for b in appreciation:
                        #     b['detail'] = bag.get('code').replace("BAG", "") + "KG"

                birth = i.get('value').get('info').get('dateOfBirth')
                if birth:
                    birth = self.DFR.format_to_transform(birth, '%Y-%m-%dT%H:%M:%S')
                    birth = birth.strftime("%Y-%m-%d")
                else:
                    birth = ""

                # 判断乘客类型
                passenger_type_code = i.get('value').get('passengerTypeCode')
                if passenger_type_code == "CHD":
                    age_type = 1
                elif passenger_type_code == "ADT":
                    age_type = 0
                else:
                    age_type = "1"

                self.passengers.append({
                    "passengerName": f"{last_name}/{first_name}",
                    "passengerBirthday": birth,
                    "passengerSex": sex,
                    "passengerType": age_type,
                    "passengerNationality": "",
                    "identificationNumber": "",
                    "cardType": "",
                    "cardExpired": "",
                    "service_type": "",
                    "auxArray": appreciation
                })

            return True

        self.logger.info("乘客超时或者错误(*>﹏<*)【passengers】")
        self.callback_msg = "乘客超时或者错误"
        return False

    def create_jwt(self, token1: str = "", url: str = ""):
        """
        生成 token
        :param token1:
        :param url:
        :return:
        """
        # 2.43.2 版本可以使用 2020-02-29 08:50

        signing_key = 'bmF2aXRhaXJlcHJvZmVzc2lvbmFsc2VydmljZXM='.encode()
        jwt = JWT()
        if token1 == "":

            ## 加密
            message = {"appname": "cebupacific", "version": "2.46.2",
                       "platform": "ANDROID", "NSToken": None, "url": url}

            compact_jws = jwt.encode(payload=message, key=OctetJWK(signing_key),
                                     alg='HS256',
                                     optional_headers={'alg': 'HS256', 'typ': 'JWT'})
            return compact_jws

        elif token1 != "":
            ## 解密
            # compact_jws = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBuYW1lIjogImNlYnVwYWNpZmljIiwgInZlcnNpb24iOiAiMi40MS4wIiwgInBsYXRmb3JtIjogIkFORFJPSUQiLCAiTlNUb2tlbiI6IG51bGwsICJ1cmwiOiAiaHR0cHM6Ly9tb2JpbGUtYXBpLmNlYnVwYWNpZmljYWlyLmNvbS9kb3RyZXotcHJvZC12My9hcGkvdjEvVG9rZW4ifQ.fAgPk8BuYSMib7eUwbhxJIaaYtd4E3F1ruoIkC7eaaQ'
            message = {"appname": "cebupacific", "version": "2.46.2", "platform": "ANDROID", "NSToken": token1,
                       "url": url}
            compact_jws = jwt.encode(payload=message, key=OctetJWK(signing_key),
                                     alg='HS256',
                                     optional_headers={'alg': 'HS256', 'typ': 'JWT'})
            return compact_jws

    # result = jwt.decode(message=message, key=OctetJWK(signing_key))
    # self.logger.info(json.dumps(result))
    # signing_key = 'bmF2aXRhaXJlcHJvZmVzc2lvbmFsc2VydmljZXM='.encode()
    # jwt = JWT()
    # ## 加密
    # message = {"appname": "cebupacific", "version": "2.41.0", "platform": "ANDROID", "NSToken": None, "url": "https://mobile-api.cebupacificair.com/dotrez-prod-v3/api/v1/Token"}
    # compact_jws = jwt.encode(payload=message, key=OctetJWK(signing_key), alg='HS256', optional_headers={'alg': 'HS256', 'typ': 'JWT'})
    ## 解密
    # compact_jws = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBuYW1lIjogImNlYnVwYWNpZmljIiwgInZlcnNpb24iOiAiMi40MS4wIiwgInBsYXRmb3JtIjogIkFORFJPSUQiLCAiTlNUb2tlbiI6IG51bGwsICJ1cmwiOiAiaHR0cHM6Ly9tb2JpbGUtYXBpLmNlYnVwYWNpZmljYWlyLmNvbS9kb3RyZXotcHJvZC12My9hcGkvdjEvVG9rZW4ifQ.fAgPk8BuYSMib7eUwbhxJIaaYtd4E3F1ruoIkC7eaaQ'
    # compact_jws = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBuYW1lIjogImNlYnVwYWNpZmljIiwgInZlcnNpb24iOiAiMi40MC4wIiwgInBsYXRmb3JtIjogIkFORFJPSUQiLCAiTlNUb2tlbiI6IG51bGwsICJ1cmwiOiAiaHR0cHM6Ly9tb2JpbGUtYXBpLmNlYnVwYWNpZmljYWlyLmNvbS9kb3RyZXotcHJvZC12My9hcGkvdjEvVG9rZW4ifQ.pwnZNkS-jy9-OyuZRrGPLJlpGtOPp67ABv5rNLlqeu8'
    # result = jwt.decode(message=compact_jws, key=OctetJWK(signing_key))

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
