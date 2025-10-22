import os

import yaml
from botpy import logging
import botpy

from ChatBot.ChatBot import ChatBotClient

_log = logging.get_logger()

class ChatBot():
    def __init__(self):
        _log.info("[ChatBot] 初始化机器人配置信息")
        ## 读取配置文件
        with open(os.path.join(os.getcwd(), "config", "config.yml"), 'r') as file:
            config: dict = yaml.safe_load(file)
            _log.info(f"[ChatBot] 机器人配置文件: {config}")

        # 订阅消息配置
        self.intents: dict = config["intents"]
        # 机器人登录配置
        self.loginToken: dict = config["botpy"]

        _log.info("初始化完成")

    def run(self):
        intents = botpy.Intents(**self.intents)
        client = ChatBotClient(intents=intents)
        client.run(**self.loginToken)