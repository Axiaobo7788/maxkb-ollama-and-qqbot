import botpy
from botpy import logging
from botpy.message import C2CMessage

from MaxKB import MaxKB

_log = logging.get_logger()

class ChatBotClient(botpy.Client):
    async def on_ready(self):
        self.maxKb = MaxKB()
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_c2c_message_create(self, message: C2CMessage):
        await message._api.post_c2c_message(
            openid=message.author.user_openid,
            msg_type=0, msg_id=message.id,
            content=self.maxKb.send_message(message)
        )