import os
import re

import requests
import yaml
from botpy import logging
from botpy.message import C2CMessage

from MaxKB.MaxKBApi import MaxKBApi

_log = logging.get_logger()


class MaxKB:
    def __init__(self):
        _log.info("[MaxKB] MaxKB 配置信息")
        ## 读取配置文件
        with open(os.path.join(os.getcwd(), "config", "MaxKB.yml"), 'r') as file:
            config: dict = yaml.safe_load(file)
            _log.info(f"[MaxKB] MaxKB配置文件: {config}")

        # 获取基础配置
        base_info = config["MaxKB"]

        # 使用字典存储聊天ID缓存,key为用户ID
        self.chat_cache = {}

        self.maxKBApi = MaxKBApi(base_info)

        _log.info(f"[MaxKB] MaxKB 初始化完成")

    def get_chat(self) -> str:
        chatId: str = self.maxKBApi.get_chat()["data"]
        return chatId

    def send_message(self, qqMessage: C2CMessage) -> str:
        _log.info(qqMessage)
        user_id = qqMessage.author.id
        
        if user_id not in self.chat_cache:
            self.chat_cache[user_id] = self.get_chat()

        req = self.maxKBApi.send_message(self.chat_cache[user_id], qqMessage.content)["data"]["content"]

        _log.info(req)

        return req

    def getMaxKBApi(self) -> MaxKBApi:
        return self.maxKBApi
