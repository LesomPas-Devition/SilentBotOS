# -*- coding: utf-8 -*-
import asyncio
import os

import botpy
from botpy import logging
from botpy.ext.cog_yaml import read
from botpy.message import C2CMessage, GroupMessage, Message
from botpy.manage import GroupManageEvent

from SilentBotOS import *

test_config = read(os.path.join(os.path.dirname(__file__), "config.yaml"))

_log = logging.get_logger()

SilentBotOS = SilentBotOS()

class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_group_add_robot(self, event: GroupManageEvent):
        _log.info("机器人被添加到群聊：" + str(event))
        await self.api.post_group_message(
            group_openid=event.group_openid,
            msg_type=0,
            event_id=event.event_id,
            content="hello",
        )

    async def on_group_del_robot(self, event: GroupManageEvent):
        _log.info("机器人被移除群聊：" + str(event))

    async def on_group_msg_reject(self, event: GroupManageEvent):
        _log.info("群聊关闭机器人主动消息：" + str(event))

    async def on_group_msg_receive(self, event: GroupManageEvent):
        _log.info("群聊打开机器人主动消息：" + str(event))

    async def on_at_message_create(self, message: Message):
        print(message)
    
    async def on_c2c_message_create(self, message: C2CMessage):
        atEvent = createAtEvent(message)
        await SilentBotOS.uploadAtEvent(atEvent)

    async def on_group_at_message_create(self, message: GroupMessage):
        atEvent = createAtEvent(message)
        await SilentBotOS.uploadAtEvent(atEvent)


if __name__ == "__main__":
    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True, public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])