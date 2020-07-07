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
"""The formatter is use for format structure data."""


class CallBackFormatter:
    """回调格式器，返回的数据格式。"""
    
    def __init__(self):
        self.logger: any = None  # 日志记录器。
    
    @classmethod
    def format_to_sync(cls) -> dict:
        """Format to sync data. 格式化同步数据。

        Returns:
            dict
        """
        sync_data = {
            "code": 400,
            "success": "false",
            "msg": "质检失败",
            "ticketNumber": "",
            "purchaseOrderStatus": "",
            "systemOrderStatus": "",
            "segments": [],
            "passengerDataList": [],
        }
        return sync_data

    @classmethod
    def format_to_async(cls) -> dict:
        """Format to sync data. 格式化异步数据。

        Returns:
            dict
        """
        async_data = {
            "code": 400,
            "success": "false",
            "msg": "质检失败",
            "ticketNumber": "",
            "purchaseOrderStatus": "",
            "systemOrderStatus": "",
            "segments": [],
            "passengerDataList": [],
        }
        return async_data
