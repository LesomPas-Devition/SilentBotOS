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

async def messageReply(message):
    atEvent = createAtEvent(message)
    if type(atEvent) == str:
        match atEvent:
            case 'NoFindCommandError':
                await message.reply(content='没有找到这条命令呢, 可以使用/help获取一些指令的信息')
            case 'ParamsNumError':
                await message.reply(content='命令参数错误了, 使用/命令名 -h查询语法，以便更方便的使用')
        return
    await SilentBotOS.uploadAtEvent(atEvent)


class MyClient(botpy.Client):
    async def on_ready(self):
        _log.info(f"robot 「{self.robot.name}」 on_ready!")

    async def on_group_del_robot(self, event: GroupManageEvent):
        _log.info("机器人被移除群聊：" + str(event))

    async def on_group_msg_reject(self, event: GroupManageEvent):
        _log.info("群聊关闭机器人主动消息：" + str(event))

    async def on_group_add_robot(self, event: GroupManageEvent):
        _log.info("机器人被添加到群聊：" + str(event))
        await self.api.post_group_message(
            group_openid=event.group_openid,
            msg_type=0,
            event_id=event.event_id,
            content="这里是SiLent酱哦<(￣3￣)y▂ξ\n使用噢\n\n/就可以找到我的功能哦\n\n'/userhelp'指令帮您了解我目前的功能\n慢慢探索吧",
        )

    async def on_group_msg_receive(self, event: GroupManageEvent):
        _log.info("群聊打开机器人主动消息：" + str(event))
        await self.api.post_group_message(
            group_openid=event.group_openid,
            msg_type=0,
            event_id=event.event_id,
            content='唔终于能说话了'
        )

    async def on_at_message_create(self, message: Message):
        print(message)
    
    async def on_c2c_message_create(self, message: C2CMessage):
        await messageReply(message)

    async def on_group_at_message_create(self, message: GroupMessage):
        await messageReply(message)

if __name__ == "__main__":
    # 通过kwargs，设置需要监听的事件通道
    intents = botpy.Intents(public_messages=True, public_guild_messages=True)
    client = MyClient(intents=intents)
    client.run(appid=test_config["appid"], secret=test_config["secret"])
