import asyncio
import botpy
from botpy import logging
from botpy.message import C2CMessage

_log = logging.get_logger()

class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_c2c_message_create(self, message: C2CMessage):
        # ✅ 使用 run_in_executor 避免阻塞
        loop = asyncio.get_running_loop()
        content = await loop.run_in_executor(
            None, self.messageService.c2c_public_message, message
        )
        
        # ✅ 可以并发处理多个用户请求
        await message._api.post_c2c_message(
            openid=message.author.user_openid,
            msg_type=0, msg_id=message.id,
            content=content
        )