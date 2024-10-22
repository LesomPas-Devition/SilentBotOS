
from ulid import ULID
from stack import Stack
from queue import Queue
from botpy.message import C2CMessage, GroupMessage, Message
import shlex
from typing import Union
from log import *
import time

from __init__ import *
BotMessage = Union[Message, C2CMessage, GroupMessage]

class AtEvent:
    def __init__(self, message: BotMessage) -> None:
        self.message = message
        self.startime = time_conversion(message.timestamp)

        self.command = ''
        self.params = []
        self.processalControl = False
        self.error = None

        match self.message:
            case GroupMessage():
                self.msgMOI = self.message.author.member_openid
                self.msgGOI = self.message.group_openid
            case C2CMessage():
                self.msgMOI = self.message.author.user_openid
                self.msgGOI = None 
            case Message():
                pass
        self.initialAtEvent = {'content': {'message': self.message}, 'msgMOI': self.msgMOI, 'msgGOI': self.msgGOI, 'time': self.startime}


    def parseCommand(self) -> None:
        """
        分离命令和参数

        args: command_string: robot_content
                 - For example: /repeat a b-> [repeat, [a, b]]

        return: None

        raise: 
           - ContentSyntaxError: 命令没以斜杠开头
           - UnknownValueError: 引号不匹配, 有可能其他的错误也会触发
        """
        command_string = self.message.content
        command_string = command_string[command_string.find('/'):]
        # 检查命令是否以'/'开头
        if not command_string.startswith('/'):
            LogWrite(atEvent=self.initialAtEvent, error='ContentSyntaxError')
            self.error = 'ContentSyntaxError'
        try:
            # 使用shlex.split来正确处理引号
            parts = shlex.split(command_string)

            # 移除所有参数中的引号，但保留'/xx'结构
            parts = [part.strip('"\'') if not part.startswith('/') or i == 0 else part for i, part in enumerate(parts)]
            self.command = parts.pop(0)[1:]
            self.params = parts

        except ValueError:
            LogWrite(atEvent=self.initialAtEvent, error='UnknownValueError')
            self.error ='UnknownValueError'


    def generatedAtEvent(self) -> str | dict:
        """
        检查所有参数, 生成AtEvent
        
        args: from message and parsed command

        return: AtEvent: 含有指令运行的必要信息 (dict) 或者错误内容 (str)

        raise:
           - NoFindCommandError: 没有找到命令, 可能的原因有命令没有注册或注册不成功
           - ParamsNumError: 参数的数量不符合注册命令的参数数量区间范围
           - InstructionConfigurationError: 命令配置错误, 触发此错误的唯一条件就是关联指令与会话控制一起配置
        """
        if self.error is not None:
            return self.error
        if self.command in commandnames:
            commandContent = Commands.__members__[self.command].value
        else:
            LogWrite(atEvent=self.initialAtEvent, error='NoFindCommandError')
            return 'NoFindCommandError'

        # check params num
        interval = commandContent['params']
        if len(self.params) == 1 and self.params[0] == '-h':
            self.params = 'helpmode'
        else:
            flag = False
            if len(interval) == 1:
                flag = len(self.params) == interval[0]
            elif len(interval) == 2:
                flag = interval[0] <= len(self.params) <= interval[1]
            if not flag:
                LogWrite(atEvent=self.initialAtEvent, error='ParamsNumError')
                self.params = (interval, self.params)
                return 'ParamsNumError'
    
        if commandContent['of'] is not None and commandContent['processalControl']:
            LogWrite(atEvent=self.initialAtEvent, error='InstructionConfigurationError')
            return 'InstructionConfigurationError'

        return {'content': {'message': self.message, 'command': self.command, 'params': self.params, 'processalControl': commandContent['processalControl'], \
                'function': commandContent['function'], 'of': commandContent['of']}, 'msgMOI': self.msgMOI, 'msgGOI': self.msgGOI, 'time': self.startime}


class SessionProcess:
    def __init__(self, atEvent: dict) -> None:
        self.pid = ULID()
        self.GOI = atEvent['msgGOI']
        self.MOI = atEvent['msgMOI']
        # 进程数据的4个方式可以自行选择
        self.__datastack = Stack()
        self.__dataqueue = Queue()
        self.__dictionary = {}
        self.__List = []

        self.command = atEvent['content']['command']
        commandContent = Commands.__members__[self.command].value
        # processalControl的4种情况: false 快速处理/1 单对单对话/2 单对多对话/3 混用(需要用户选择模式)
        self.sessionType = commandContent['processalControl']

        SilentBotOS.PidRunning[self.pid] = self
        if type(atEvent['content']['message']) == C2CMessage:
            self.convertedInto(1, atEvent)
            return
        match self.sessionType:
            case 1:
                UpdateDict(SilentBotOS.SessionOnePid, self.MOI, self.pid)
            case 2:
                UpdateDict(SilentBotOS.SessionTwoPid, self.GOI, self.pid)
            case 2.5:
                SilentBotOS.SessionMember[self.MOI] = {self.pid}
                UpdateDict(SilentBotOS.SessionManyTwoPid, self.GOI, self.pid)
        UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)


    def release(self) -> None:
        """
        释放进程资源
        """
        del self.__dataqueue, self.__datastack
        self.__dictionary.clear()
        self.__List.clear()

        def clear_dict(dictionary, key, value) -> None:
            if key not in dictionary:
                return None

            s = dictionary[key]
            if value not in s:
                return None

            if len(s) == 1:
                del dictionary[key]
            else:
                s.remove(value)

        pid = self.pid
        # 根据会话类型清理关联的映射
        if self.sessionType == 1:
            clear_dict(SilentBotOS.SessionOnePid, self.MOI, pid)
        elif self.sessionType == 2:
            clear_dict(SilentBotOS.SessionTwoPid, self.GOI, pid)
        elif self.sessionType == 2.5:
            clear_dict(SilentBotOS.SessionMember, self.MOI, pid)
            clear_dict(SilentBotOS.SessionManyTwoPid, self.GOI, pid)

        # 清理命令到进程的映射
        clear_dict(SilentBotOS.CommandPid, self.command, pid)


    def convertedInto(self, SessionType: int, atEvent: dict) -> None:
        MOI = atEvent['msgMOI']
        GOI = atEvent['msgGOI']
        match SessionType:
            case 1:
                UpdateDict(SilentBotOS.SessionOnePid, MOI, self.pid)
            case 2:
                UpdateDict(SilentBotOS.SessionTwoPid, GOI, self.pid)
            case 2.5:
                SilentBotOS.SessionMember[MOI] = {self.pid}
                UpdateDict(SilentBotOS.SessionManyTwoPid, GOI, self.pid)
        UpdateDict(SilentBotOS.CommandPid, self.command, self.pid)
        self.sessionType = SessionType

    def UpdateLastCallTime(self):
        SilentBotOS.ProcessLastCallTime[self.pid] = time.time()

    @property
    def List(self):
        self.UpdateLastCallTime()
        return self.__List
    @property
    def dictionary(self):
        self.UpdateLastCallTime()
        return self.__dictionary
    @property
    def queue(self):
        self.UpdateLastCallTime()
        return self.__dataqueue
    @property
    def stack(self):
        self.UpdateLastCallTime()
        return self.__datastack

    def save(self, queue=None, stack=None, List=None, dictionary=None) -> None:
        if queue is not None:
            self.__dataqueue = queue
        if stack is not None:
            self.__datastack = stack
        if List is not None:
            self.__List = List
        if dictionary is not None:
            self.__dictionary = dictionary


def createAtEvent(message: BotMessage) -> None | dict:
    atEvent = AtEvent(message)
    atEvent.parseCommand()
    result = atEvent.generatedAtEvent()
    del atEvent
    return result


def createReturnEvent(messageResult: dict, content: str, atEvent: dict) -> dict:
    if messageResult is None:
        LogWrite(atEvent=atEvent, error='MessageResultLoadError')
        return {'time': atEvent['time'], 'information': atEvent['content']['message'].content}
    return {'time': time_conversion(messageResult['timestamp']), 'information': content}


async def replyMessage(content: str, atEvent: dict, sequence=-1) -> None:
    message = atEvent['content']['message']
    if sequence == -1:
        SilentBotOS.MessageSequence = SilentBotOS.MessageSequence % (SilentBotOS.SequenceFrequencyDomain[1] - SilentBotOS.SequenceFrequencyDomain[0] + 1) \
                                                                  + SilentBotOS.SequenceFrequencyDomain[0]
        sequence = SilentBotOS.MessageSequence

    messageResult = await message.reply(content=content, msg_seq=sequence)
    returnEvent = createReturnEvent(messageResult, content, atEvent)
    LogWrite(atEvent)
    LogWrite(atEvent, returnEvent)


class SilentBotOS:
    _instance = None

    SequenceFrequencyDomain = (101, 200)
    MessageSequence = SequenceFrequencyDomain[1] - SequenceFrequencyDomain[0] + 1

    ProcessRecoveryTime = 300
    ProcessLastCallTime = {}

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
    def findProcess(atEvent: dict) -> str | list[ULID]:
        """
        根据atEvent查找或生成进程
        
        arg: atEvent
        return: SessionProcess | list[ULID]
        """
        command = atEvent['content']['command'] if (p := atEvent['content']['of']) is None else p # 关联指令检测
        MOI = atEvent['msgMOI']
        GOI = atEvent['msgGOI']
        messageType = type(atEvent['content']['message'])
        sessionType = Commands.__members__[command].value['processalControl']

        def _Intersection(set1, set2, key1, key2) -> list | SessionProcess:
            try: return list(set1[key1] & set2[key2])
            except KeyError: return None

        def _ProcessIntersection(set1, set2, key1, key2, returnlist=False, atEvent=None) -> ULID | list:
            try:
                if (result := _Intersection(set1, set2, key1, key2)) is None:
                    return SessionProcess(atEvent) if not returnlist else [SessionProcess(atEvent)]
                return SilentBotOS.PidRunning(result[0]) if not returnlist else result
            except IndexError: pass

        match sessionType:
            case 1:
                return _ProcessIntersection(SilentBotOS.SessionOnePid, SilentBotOS.CommandPid, MOI, command, atEvent=atEvent)
            case 2:
                if messageType == C2CMessage:
                   return _ProcessIntersection(SilentBotOS.SessionOnePid, SilentBotOS.CommandPid, MOI, command, atEvent=atEvent)
                return _ProcessIntersection(SilentBotOS.SessionTwoPid, SilentBotOS.CommandPid, GOI, command, atEvent=atEvent)
            case 2.5:
                if messageType == C2CMessage:
                    return _ProcessIntersection(SilentBotOS.SessionOnePid, SilentBotOS.CommandPid, MOI, command, returnlist=True, atEvent=atEvent)
                try:
                    process = _Intersection(SilentBotOS.SessionManyTwoPid, SilentBotOS.SessionMember, GOI, MOI)[0]
                    if SilentBotOS.PidRunning[process].command == command:
                        return [process]
                except Exception: pass

                return _ProcessIntersection(SilentBotOS.SessionManyTwoPid, SilentBotOS.CommandPid, GOI, command, returnlist=True, atEvent=atEvent)


    async def uploadAtEvent(self, atEvent: dict | str) -> None:
        SilentBotOS.release()
        if type(atEvent) == str:    #atEvent是否为错误信息
            return atEvent
        processalControl = atEvent['content']['processalControl']
        # 检测不是会话控制状态与关联指令
        if not processalControl and atEvent['content']['of'] is None:
            await SilentBotOS.fastParse(atEvent)
            return

        # 是否为关联指令
        if atEvent['content']['of'] is not None and not processalControl:
            command = atEvent['content']['of']
            commandContent = Commands.__members__[command].value
        else:
            command = atEvent['content']['command']
            commandContent = Commands.__members__[command].value

        sessionType = commandContent['processalControl']
        function = atEvent['content']['function']
        message = atEvent['content']['message']

        match sessionType:
            case 1 | 2:
                process = SilentBotOS.findProcess(atEvent)
            case 2.5:
                process = SilentBotOS.findProcess(atEvent)
                try:
                    if atEvent['content']['params'][-1] == '+':
                        if type(message) == C2CMessage and len(SilentBotOS.SessionOnePid.get(atEvent['msgMOI'])) >= 1:
                            await replyMessage("私聊中不可创建第二个重复进程", atEvent)
                            return
                        del atEvent['content']['params'][-1]
                        process = SessionProcess(atEvent)
                        await replyMessage(f'{function(atEvent, process)}\n\nPid:{process.pid}', atEvent)
                        return
                except IndexError: pass

                if len(process) != 1:
                    attention = "出现了多个可用进程, 请使用/switching <pid> 去选择进程\n\n"
                    for i in process: attention += f'{i}\n'
                    await replyMessage(attention, atEvent)
                    return

                process = SilentBotOS.PidRunning[process[0].pid]

        await replyMessage(f'{function(atEvent, process)}\n\nPid:{process.pid}', atEvent)

    @classmethod
    def release(cls) -> None:
        def _releaseProcess(cls, pid) -> None:
            try:
                process = cls.PidRunning[pid]
            except KeyError: return

            process.release()
            del cls.PidRunning[pid]
            del process

        now = time.time()
        for item in cls.ProcessLastCallTime.items():
            if now - item[1] > cls.ProcessRecoveryTime:
                _releaseProcess(cls, item[0])
