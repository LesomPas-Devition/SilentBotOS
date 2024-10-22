
from typing import Union
from ulid import ULID
from botpy.message import C2CMessage, GroupMessage, Message
import json
from UGC import UserGeneratedContent
from random import choice

class DRVCommands: # Determined ReturnValue Commands
    @staticmethod
    def cello(atEvent: dict):
        if atEvent['content']['params'] == 'helpmode':
            return (
                "\n功能: 恭喜你发现了这一个彩蛋\n"
                "语法: /cello"
            )
        return "\n Ciallo～(∠・ω< )⌒☆"

    @staticmethod
    def userhelp(atEvent: dict):
        if atEvent['content']['params'] == 'helpmode':
            return "恭喜你发现第二个彩蛋:\n《在帮助中使用帮助》"
        helpText = (
            "\n下面是一些关于使用指令的通用注意事项\n这一段文字的末尾将给出目前所有的指令\n"
            "1.在命令名后加上'-h'可以获得有关该指令的功能语法和注意事项的说明(如果某一项没写会省略)\n"
            "2.如果你要把带有空格的消息视为一个整体传入到参数中请用英文引号包裹文本, 否则可能会有语法错误\n"
            "(其实如果你的文本很复杂的话，建议直接包括引号\n"
            "目前所有的命令:\n"
            "登陆类: /enroll, /sign /rename\n"
            "正常类: /repeat, /DriftBottle或/漂流瓶\n"
            "其他类: /switching, /AAPs"
        )

        return helpText

class NormalCommands:
    @staticmethod
    def repeat(atEvent: dict):
        if atEvent['content']['params'] == 'helpmode':
            return (
                "\n功能: 重复用户输入内容\n"
                "语法: /repeat <重复信息>"
            )
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
        if atEvent['content']['params'] == 'helpmode':
            return (
                "\n功能: 签到打卡\n"
                "语法: /sign [AdminPassword]"
            )
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
        if atEvent['content']['params'] == 'helpmode':
            return (
                "\n功能: 更改账户名称\n"
                "语法: /rename <名称>"
            )
        memberList = SignCommands._getMemberList()
        MOI = atEvent['msgMOI']

        if MOI not in memberList['members']:
            return "你还没注册过账号呢, 使用/enroll命令就可以注册哦(K酱提醒您)"

        memberList['members'][MOI]['name'] = atEvent['content']['params'][0]
        SignCommands._ioJsonData(cls.memberPath, 'w', content=memberList)
        return '更改成功了喵'


    @classmethod
    def enroll(cls, atEvent: dict):
        if atEvent['content']['params'] == 'helpmode':
            return (
                "\n功能: 创建新账户(发布内容要用)\n"
                "语法: /enroll"
            )
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


    @classmethod
    def _isAdmin(cls, atEvent: dict) -> bool:
        memberList = SignCommands._getMemberList()
        MOI = atEvent["msgMOI"]

        if MOI not in memberList["members"] or MemberList['members'][MOI]['admin'] is None:
            return False

        return MemberList['members'][MOI]['admin']['adminMode']

    @staticmethod
    def _ioJsonData(path: str, mode: Union['r', 'w'], content=None):
        js = open(path, mode, encoding="utf-8")
        if mode == 'w':
            json.dump(content, js, ensure_ascii=False, indent=4)
        elif mode == 'r':
            result = json.load(js)
            return result

    def _getMemberList():
        return SignCommands._ioJsonData('./Data/Member.json', 'r')


class DriftBottleCommands:
    @staticmethod
    def main(atEvent: dict) -> None:
        params = atEvent["content"]["params"]
        if type(params) == tuple:
            return "参数数量不对呢, 建议检查一下"
        if params == "helpmode":
            return (
                "\n功能: 捡起或扔出漂流瓶\n"
                "语法: /DriftBottle throw <内容>\n"
                "     /DriftBottle pick\n"
                "     /漂流瓶 扔出 <内容>\n"
                "     /漂流瓶 捡起\n"
                "注意事项: 建议在扔出漂流瓶时将内容用引号包裹.且只能保存一张图片"
            )

        if params[0] not in ["throw", "pick", "捡起", "扔出"]:
            return "第一项参数不对呢, 使用'/漂流瓶 -h'查看帮助哦"

        if params[0] == "pick" or params[0] == "捡起":
            sea = SignCommands._ioJsonData("./Data/sea.json", "r")
            try:
                seakey = choice(list(sea.keys()))
                seavalue = sea[seakey]
            except IndexError:
                return "大海上空无一物呢"
            if atEvent["msgGOI"] not in seavalue["browsed"]:
                seavalue["browsed"].append(atEvent["msgGOI"])
                sea[seakey] = seavalue
                SignCommands._ioJsonData("./Data/sea.json", "w", content=sea)
                return seavalue["content"]["text"] + f'\n\n——{seavalue["time"]}'
            else:
                return "这次你还没有捡到瓶子哦, 再试一次也许就可以了哦"

        if params[0] == "throw" or params[0] == "扔出":
            UserGeneratedContent("DriftBottle", atEvent["msgMOI"], {"text": params[1], "url": []}, atEvent["time"]).SavaByDriftBottle(atEvent['msgGOI'])
            return "你向大海中抛出了一个瓶子, 期待未来有机会有人能够捡到ta"


class DirectedCommands:
    @staticmethod
    def count(atEvent: dict, process: 'SessionProcess'):
        queue = process.queue
        if queue.empty():
            queue.put(1)
            return "1"
        num = queue.get()
        queue.put(num + 1)
        process.save(queue=queue)
        return str(num + 1)

    @staticmethod
    def lessen(atEvent: dict, process: 'SessionProcess'):
        queue = process.queue
        if queue.empty():
            queue.put(0)
            return "0"
        num = queue.get()
        queue.put(num - 1)
        process.save(queue=queue)
        return str(num - 1)


class SystemCommands:
    @staticmethod
    def switching(atEvent: dict):  # for SessionType is 2.5
        if atEvent['content']['params'] == 'helpmode':
            return (
                "\n功能: 切换进程\n"
                "语法: /switching <pid>\n"
                "特殊说明:\n"
                "1.私信中不可使用/switching\n"
                "2.只能切换命令创建进程类型为2.5的进程"
            )
        if type(atEvent["content"]["message"]) == C2CMessage:
            return "私信环境中不可使用/switching"
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

    @staticmethod
    def allAvailableProcesses(atEvent: dict) -> str:
        if atEvent['content']['params'] == 'helpmode':
            return (
                "\n功能: 给出当前所有的运行进程\n"
                "语法: /AAPs\n"
                "特殊说明:\n"
                "1.AAPs为all available processes的缩写\n"
                "2.该指令仅限管理员使用, 因为过量的进程运行列表可能占用聊天内容"
            )
        def _print(dictionary, header: str) -> str:
            result = f"{header}\n"
            for i in dictionary.values():
                result += (str(i) + "\n")
            result += "\n"
            return result

        from SilentBotOS import SilentBotOS
        a = _print(SilentBotOS.SessionOnePid, "Session 1:")
        commands = _print(SilentBotOS.CommandPid, "Commands:")
        b = _print(SilentBotOS.SessionTwoPid, "Session 2:")
        c = _print(SilentBotOS.SessionManyTwoPid, "Session 2.5:")
        d = _print(SilentBotOS.SessionMember, "Personal Session")
        return a + b + c + d + commands
