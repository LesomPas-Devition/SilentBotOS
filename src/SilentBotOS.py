
from ulid import ULID
from stack import Stack
from queue import Queue
from botpy.message import C2CMessage, GroupMessage, Message
from typing import Union
import shlex
from random import randint
from log import *

from __init__ import *
BotMessage = Union[Message, C2CMessage, GroupMessage]

class AtEvent:
    def __init__(self, message: BotMessage) -> None:
        self.message = message
        self.startime = time_conversion(message.timestamp)

        self.command = ''
        self.params = []
        self.processalControl = False

        match self.message:
            case GroupMessage():
                self.msgMOI = self.message.author.member_openid
                self.msgGOI = self.message.group_openid
            case C2CMessage():
                self.msgMOI = self.message.author.user_openid
                self.msgGOI = None 
            case Message():
                pass


    def parseCommand(self) -> None:
        """
        分离命令和参数

        args:
            command_string: robot_content
                For example: /repeat a b-> [repeat, [a, b]]

        return:
            None

        raise:
            ContentSyntaxError: 命令没以斜杠开头或者不匹配
        """
        command_string = self.message.content
        command_string = command_string[command_string.find('/'):]
        # 检查命令是否以'/'开头
        if not command_string.startswith('/'):
            print("Error: Command must start with '/'")

        try:
            # 使用shlex.split来正确处理引号
            parts = shlex.split(command_string)

            # 移除所有参数中的引号，但保留'/xx'结构
            parts = [part.strip('"\'') if not part.startswith('/') or i == 0 else part for i, part in enumerate(parts)]
            self.command = parts.pop(0)[1:]
            self.params = parts

        except ValueError as e:
            # 处理引号不匹配等错误
            print(f"Error parsing command: {e}")


    def generatedAtEvent(self) -> str | dict:
        """
        检查所有参数, 生成AtEvent
        
        args:
            from message and parsed command

        return:
            AtEvent: 含有指令运行的必要信息 (dict)

        raise:
            noFindCommandError: 没有找到命令, 可能的原因有命令没有注册或注册不成功
            paramsNumError: 参数的数量不符合注册命令的参数数量区间范围
        """

        if self.command in commandnames:
            commandContent = Commands.__members__[self.command].value
        else:
            return 'noFindCommandError'

        # check params num
        interval = commandContent['params']
        if not (len(interval) == 1 and len(self.params) == interval[0] or \
                len(interval) == 2 and interval[0] <= len(self.params) <= interval[1]):
            return 'paramsNumError'

        return {'content': {'message': self.message, 'command': self.command, 'params': self.params, 'processalControl': commandContent['processalControl'], \
                'function': commandContent['function'], 'of': commandContent['of']}, 'msgMOI': self.msgMOI, 'msgGOI': self.msgGOI, 'time': self.startime}


class SessionProcess:
    def __init__(self, atEvent: dict) -> None:
        self.pid = ULID()
        self.GOI = atEvent['msgGOI']
        self.MOI = atEvent['msgMOI']
        # 进程数据的4个方式可以自行选择
        self.datastack = Stack()
        self.dataqueue = Queue()
        self.dictionary = {}
        self.List = []

        self.command = atEvent['content']['command']
        commandContent = Commands.__members__[self.command].value
        # processalControl的4种情况: false 快速处理/1 单对单对话/2 单对多对话/3 混用(需要用户选择模式)
        self.sessionType = commandContent['processalControl']

        SilentBotOS.PidRunning[self.pid] = self
        match self.sessionType:
            case 1:
                UpdateDict(SilentBotOS.SessionOnePid, self.MOI, self.pid)
                UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)
            case 2:
                UpdateDict(SilentBotOS.SessionTwoPid, self.GOI, self.pid)
                UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)
            case 2.5:
                SilentBotOS.SessionMember[self.MOI] = {self.pid}
                UpdateDict(SilentBotOS.SessionManyTwoPid, self.GOI, self.pid)
                UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)


def createAtEvent(message: BotMessage) -> None | dict:
    match message:
        case GroupMessage():
            atEvent = AtEvent(message)
            atEvent.parseCommand()
            result = atEvent.generatedAtEvent()
            del atEvent
            return result

        case C2CMessage():
            atEvent = AtEvent(message)
            atEvent.parseCommand()
            result = atEvent.generatedAtEvent()
            del atEvent
            return result

        case Message():
            ...


def createReturnEvent(messageResult: dict, content: str) -> dict:
    return {'time': time_conversion(message.timestamp), 'content': content}


def replyMessage(message: BotMessage, content: str, atEvent: dict, sequence=-1) -> None:
    if sequence == -1:
        SilentBotOS.MessageSequence += 1
        sequence = SilentBotOS.MessageSequence

    messageResult = await message.reply(content=content, msg_seq=sequence)
    returnEvent = createReturnEvent(messageResult, content)
    LogWrite(atEvent)
    LogWrite(atEvent, returnEvent)


class SilentBotOS:
    _instance = None
    MessageSequence = 0

    PidRunning = {}

    SessionOnePid = {}
    CommandPid = {}

    SessionTwoPid = {}

    SessionManyTwoPid = {}
    SessionMember = {}

    def __new__(cls, *args, **kwargs) -> 'SilentBotOS':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance


    @staticmethod
    async def fastParse(atEvent: dict) -> None:
        message = atEvent['content']['message']
        function = atEvent['content']['function']
        messageResult = await message.reply(content=function(atEvent), msg_seq=randint(2, 4))

        return messageResult


    @staticmethod
    def findProcess(atEvent: dict) -> str | list[str]:
        if atEvent['content']['of'] is None:
            command = atEvent['content']['command']
        else:
            command = atEvent['content']['of']
        MOI = atEvent['msgMOI']
        GOI = atEvent['msgGOI']
        messageType = type(atEvent['content']['message'])
        commandContent = Commands.__members__[command].value
        sessionType = commandContent['processalControl']
        
        match sessionType:
            case 1:
                try:
                    processesA = SilentBotOS.SessionOnePid[MOI]
                    processesB = SilentBotOS.CommandPid[command]

                    process = processesA & processesB
                    return [list(process)[0].pid]

                except KeyError:
                    return [SessionProcess(atEvent).pid]


            case 2:
                if messageType == C2CMessage:
                    return 'error'
                try:
                    processesA = SilentBotOS.SessionTwoPid[GOI]
                    processesB = SilentBotOS.CommandPid[command]

                    process = processesA & processesB
                    return [list(process)[0].pid]

                except KeyError:
                    return [SessionProcess(atEvent).pid]

            case 2.5:
                if messageType == C2CMessage:
                    return 'error'
                try:
                    processesA = SilentBotOS.SessionManyTwoPid[GOI]
                    processesB = SilentBotOS.SessionMember[MOI]

                    process = list(processesA & processesB)[0]

                    if SilentBotOS.PidRunning[process].command == atEvent['content']['command']:
                        return [SilentBotOS.PidRunning[process].pid]
                except KeyError:
                    pass

                try:
                    processesA = SilentBotOS.SessionManyTwoPid[GOI]
                    processesB = SilentBotOS.CommandPid[command]

                    process = list(processesA & processesB)
                    return process
                except KeyError:
                    return [SessionProcess(atEvent).pid]


    async def uploadAtEvent(self, atEvent: dict) -> None:
        try:
            processalControl = atEvent['content']['processalControl']
        except Exception:
            print(atEvent)
            return

        if not processalControl and atEvent['content']['of'] is None:
            print(await SilentBotOS.fastParse(atEvent))
            return
        
        if atEvent['content']['of'] is None:
            command = atEvent['content']['command']
            commandContent = Commands.__members__[command].value
        else:
            command = atEvent['content']['of']
            commandContent = Commands.__members__[command].value
        sessionType = commandContent['processalControl']
        function = atEvent['content']['function']
        message = atEvent['content']['message']

        match sessionType:
            case 1:
                process = SilentBotOS.PidRunning[SilentBotOS.findProcess(atEvent)[0]]
            case 2:
                process = SilentBotOS.PidRunning[SilentBotOS.findProcess(atEvent)[0]]
                if process == "error":
                    ...
            case 2.5:
                process = SilentBotOS.findProcess(atEvent)

                try:
                    if atEvent['content']['params'][-1] == '+':
                        del atEvent['content']['params'][-1]
                        process = SessionProcess(atEvent)
                        await message.reply(content=f'{function(atEvent, process)}\n\nPid:{process.pid}', msg_seq=12)
                        return
                except IndexError:
                    ...

                if process == "error":  # 添加对错误情况的检查
                    ...
                elif len(process) == 1:
                    process = SilentBotOS.PidRunning[process[0]]
                else:
                    attention = ...
                    await message.reply(content=attention)
                    return

                await message.reply(content=f'{function(atEvent, process)}\n\nPid:{process.pid}', msg_seq=12)
