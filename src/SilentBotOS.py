
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
                if type(atEvent['content']['message']) == C2CMessage:
                    self.convertedInto(1, atEvent)
                    return
                UpdateDict(SilentBotOS.SessionTwoPid, self.GOI, self.pid)
                UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)
            case 2.5:
                if type(atEvent['content']['message']) == C2CMessage:
                    self.convertedInto(1, atEvent)
                    return
                SilentBotOS.SessionMember[self.MOI] = {self.pid}
                UpdateDict(SilentBotOS.SessionManyTwoPid, self.GOI, self.pid)
                UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)


    def release(self) -> None:
        """
        释放进程资源
        """
        del self.dataqueue, self.datastack
        self.dictionary.clear()
        self.List.clear()

        pid = self.pid
        # 根据会话类型清理关联的映射
        if self.sessionType == 1:
            SilentBotOS.SessionOnePid[self.MOI].discard(pid)
        elif self.sessionType == 2:
            SilentBotOS.SessionTwoPid[self.GOI].discard(pid)
        elif self.sessionType == 2.5:
            SilentBotOS.SessionMember[self.MOI].discard(pid)
            SilentBotOS.SessionManyTwoPid[self.GOI].discard(pid)

        # 清理命令到进程的映射
        SilentBotOS.CommandPid[self.command].discard(pid)


    def convertedInto(self, SessionType: int, atEvent: dict) -> None:
        """
        match self.sessionType:
            case 1:
                SilentBotOS.SessionOnePid[self.MOI].discard(pid)
            case 2:
                SilentBotOS.SessionTwoPid[self.GOI].discard(pid)
            case 2.5:
                SilentBotOS.SessionMember[self.MOI].discard(pid)
                SilentBotOS.SessionManyTwoPid[self.GOI].discard(pid)
        """
        MOI = atEvent['msgMOI']
        GOI = atEvent['msgGOI']
        match SessionType:
            case 1:
                UpdateDict(SilentBotOS.SessionOnePid, MOI, self.pid)
            case 2:
                UpdateDict(SilentBotOS.SessionTwoPid, GOI, self.pid)
            case 2.5:
                SilentBotOS.SessionMember[MOI] = {self.pid}
                UpdateDict(SilentBotOS.SessionManyTwoPid, ;GOI, self.pid)
            UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)
            self.sessionType = SessionType


def createAtEvent(message: BotMessage) -> None | dict:
    atEvent = AtEvent(message)
    atEvent.parseCommand()
    result = atEvent.generatedAtEvent()
    del atEvent
    return result


def createReturnEvent(messageResult: dict, content: str) -> dict:
    return {'time': time_conversion(message.timestamp), 'content': content}


async def replyMessage(content: str, atEvent: dict, sequence=-1) -> None:
    message = atEvent['content']['message']
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
        await replyMessage(function(atEvent), atEvent)


    @staticmethod
    def findProcess(atEvent: dict) -> str | list[str]:
        if atEvent['content']['of'] is None: # 关联指令检测
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
        try:    #atEvent是否为错误信息
            processalControl = atEvent['content']['processalControl']
        except Exception:
            print(atEvent)
            return
        # 检测不是会话控制状态与关联指令
        if not processalControl and atEvent['content']['of'] is None:
            print(await SilentBotOS.fastParse(atEvent))
            return

        # 是否为关联指令
        if atEvent['content']['of'] is None or processalControl:
            command = atEvent['content']['command']
            commandContent = Commands.__members__[command].value
        else:
            if processalControl:
                ...
                return
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
                        await replyMessage(f'{function(atEvent, process)}\n\nPid:{process.pid}', atEvent)
                        return
                except IndexError:
                    pass

                if process == "error":  # 添加对错误情况的检查
                    ...
                elif len(process) == 1:
                    process = SilentBotOS.PidRunning[process[0]]
                else:
                    attention = "出现了多个可用进程, 请使用/switching <pid> 去选择进程\n\n"
                    for i in process:
                        attention += f'{i}\n'
                    await replyMessage(attention, atEvent)
                    return

                await replyMessage(f'{function(atEvent, process)}\n\nPid:{process.pid}', atEvent)


    def releaseProcess(pid) -> None:
        try:
            process = SilentBotOS.PidRunning[pid]
        except KeyError:
            print("invited pid")
            return

        process.release()
        SilentBotOS.PidRunning.discard(pid)
        del process
