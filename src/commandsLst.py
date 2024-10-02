
from typing import Union
from ulid import ULID

class DRVCommands: # Determined ReturnValue Commands
    @staticmethod
    def cello(atEvent: dict):
        return "\n Ciallo～(∠・ω< )⌒☆"

    @staticmethod
    def userhelp(atEvent: dict):

        helpText = (
            "1. help: 寻求帮助信息(这个有用吗)."
            "2. repeat: 重复群u输入功能."
            "3. sign: 第一次使用时, 将自动注册一个新账号. 之后就是正常的登录功能."
            "4. 我要改名: 字面意思"
        )

        return helpText

class NormalCommands:
    @staticmethod
    def repeat(atEvent: dict):
        return atEvent['content']['params'][0]


class SignCommands:
    memberPath = "./Data/Member.json"
    signPath = "./Data/TodaySign.json"

    def _date_to_string(time_str) -> str:
        # 将字符串转换为datetime对象
        time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        hour = time_obj.hour

        hour_to_str = [
            "这位群u这么晚还不睡吗?(哈欠), 你不睡我可睡了💤",
            "这位群u您起来的真早! 早安哦🥳",
            "中午好哦这位群u, 又是美好(没好bushi)的一天|ω・）",
            "这位群u下午好口牙, 要不要来点儿下午茶? 和我一起?! 好吧(脸红 ˃ʍ˂ )...",
            "晚上好, 有什么能帮助您的吗Ｏ(≧▽≦)Ｏ(应某人要求)",
        ]

        if 0 <= hour < 6 or 23 <= hour <= 24:
            return cls.hour_to_str[0]
        elif 6 <= hour < 8:
            return cls.hour_to_str[1]
        elif 8 <= hour < 13:
            return cls.hour_to_str[2]
        elif 13 <= hour < 17:
            return cls.hour_to_str[3]
        elif 17 <= hour < 23:
            return cls.hour_to_str[4]

    @classmethod
    def sign(cls, atEvent: dict):
        memberList = SignCommands._getMemberList()
        todaySign = SignCommands._ioJsonData(cls.signPath, 'r')
        MOI = atEvent['msgMOI']

        if MOI not in memberList['members']:
            return "你还没注册过账号呢, 使用/enroll命令就可以注册哦(K酱提醒您)"

        if len(atEvent['content']['params']) == 1:
            password = atEvent['content']['params'][0]
            return SignCommands._administratorSign(MOI, memberList, password)

        creditPoint = memberList['members'][MOI]['creditPoint']
        name = memberList['members'][MOI]['name']

        if MOI in todaySign:
            repeated_sign = ("\n这位群u ({})已经在{}签过了哦, 当前您的信用点为{}"
                             "\n➡️使用'/help'可以获得更多有趣的命令的帮助哦awa")
            signTime = todaySign[MOI]['time']
            return repeated_sign.format(name, signTime, creditPoint)

        successful_sign = ("\n现在时间: {}, {}"
                           "\n\n这位群u ({})您获得了12个信用点, 当前您的信用点为{}()"
                           "\n\n祝您今日愉快哦φ(≧ω≦*)♪"
                           "\n\n➡️使用'/help'可以获得所有命令的帮助哦awa")

        memberList['members'][MOI]['creditPoint'] = creditPoint + 12
        creditPoint = memberList['members'][MOI]['creditPoint']
        time = atEvent['time']
        todaySign[MOI] = {'time': time}

        SignCommands._ioJsonData(cls.memberPath, 'w', content=memberList)
        SignCommands._ioJsonData(cls.signPath, 'w', content=todaySign)
        return successful_sign.format(time, SignCommands._data_to_string(time), name, creditPoint)


    @classmethod
    def rename(cls, atEvent: dict):
        memberList = SignCommands._getMemberList()
        MOI = atEvent['msgMOI']

        if MOI not in memberList['members']:
            return "你还没注册过账号呢, 使用/enroll命令就可以注册哦(K酱提醒您)"

        memberList['members'][MOI]['name'] = atEvent['content']['params'][0]
        SignCommands._ioJsonData(cls.memberPath, 'w', content=memberList)
        return '更改成功了喵'


    @classmethod
    def enroll(cls, atEvent: dict):
        memberList = SignCommands._getMemberList()
        MOI = atEvent['msgMOI']

        if MOI in memberList['members']:
            return "你已经注册过账号了哦(K酱提醒您)"

        username_start = memberList['order']
        memberList['members'][MOI] = {'name': f'user{username_start}', 'creditPoint': 0, 'admin': None}
        
        memberList['order'] += 1
        SignCommands._ioJsonData(cls.memberPath, 'w', content=memberList)
        return f"欢迎新成员! 系统分配的名称为: user{username_start} 欢迎使用 SilentK酱_ (/≧▽≦)/\n"  # 新人欢迎+注册账号提醒


    @classmethod
    def _administratorSign(cls, MOI: str, MemberList: dict, password: str) -> str:
        if MemberList['members'][MOI]['admin'] is None:
            return "您不是管理员, 请核对信息"

        if password == "exit":
            MemberList['members'][MOI]['admin']['adminMode'] = False
            return "已退出管理员模式"

        elif password != MemberList['members'][MOI]['admin']['password']:
            return "密码错误"

        MemberList['members'][MOI]['admin']['adminMode'] = True

        SignCommands._ioJsonData(cls.memberPath, 'w', content=MemberList)
        return "成功以管理员身份登录"


    def _ioJsonData(path: str, mode: Union['r', 'w'], content=None):
        js = open(path, mode, encoding="utf-8")
        if mode == 'w':
            json.dump(content, js, ensure_ascii=False, indent=4)
        elif mode == 'r':
            result = json.load(js)
            return result

    def _getMemberList():
        return SignCommands._ioJsonData('./Data/Member.json', 'r')


class DirectedCommands:
    @staticmethod
    def count(atEvent: dict, process: 'SessionProcess'):
        if process.dataqueue.empty():
            process.dataqueue.put(1)
            return "1"
        num = process.dataqueue.get()
        process.dataqueue.put(num + 1)
        return str(num + 1)

    @staticmethod
    def lessen(atEvent: dict, process: 'SessionProcess'):
        if process.dataqueue.empty():
            process.dataqueue.put(0)
            return "0"
        num = process.dataqueue.get()
        process.dataqueue.put(num - 1)
        return str(num - 1)


class SystemCommands:
    @staticmethod
    def join(atEvent):  # for SessionType is 1 or 3
        ...

    @staticmethod
    def switching(atEvent: dict):  # for SessionType is 2.5
        from SilentBotOS import SilentBotOS, SessionProcess
        MOI = atEvent['msgMOI']
        pid = atEvent['content']['params'][0]
        try:
            process = SilentBotOS.PidRunning[ULID.from_str(pid)]
        except KeyError:
            return "输入内容有误或者进程不存在"
        if process.sessionType == 2.5:
            SilentBotOS.SessionMember[MOI] = {ULID.from_str(pid)}
            return "切换成功"
        return "会话空间类型不符"