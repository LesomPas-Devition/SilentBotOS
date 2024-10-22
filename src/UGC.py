from ulid import ULID
from enum import Enum
import json

class UGCType(Enum):
    DriftBottle = "DriftBottle"

class UserGeneratedContent:
    def __init__(self, ContentType: str, author: str, content: dict, time: str) -> None:
        if UGCType.__members__.get(ContentType) is not None:
            self.ContentType = ContentType
        else:
            raise ValueError(f"ContentType {ContentType} is not exist")
        self.ugcID = str(ULID())
        self.author = author
        self.content = content
        self.views = 0
        self.like_dislike = [0, 0]
        self.time = time


    def AddViews(self, num=1):
        if type(num) != int:
            ValueError("num argument must be a int")
        self.views += num


    def OperationLike(self, operation: str, num=1) -> None:
        if type(num) != int:
            ValueError("num argument must be a int")

        if operation not in ["add", "lessen"]:
            return None

        if operation == "add":
            self.like_dislike[0] += num
        else:
            self.like_dislike[0] -= num


    def OperationDislike(self, operations: str, num=1) -> None:
        if type(num) != int:
            ValueError("num argument must be a int")

        if operation not in ["add", "lessen"]:
            return None

        if operation == "add":
            self.like_dislike[1] += num
        else:
            self.like_dislike[1] -= num


    def SavaByDriftBottle(self, openid) -> None:
        sea = UserGeneratedContent._ioJsonData("./Data/sea.json", "r")
        sea[self.ugcID] = {"type": self.ContentType, "author": self.author, "time": self.time, "content": self.content, "browsed": [openid,]}
        UserGeneratedContent._ioJsonData("./Data/sea.json", "w", content=sea)


    @staticmethod
    def _ioJsonData(path: str, mode, content=None):
        js = open(path, mode, encoding="utf-8")
        if mode == 'w':
            json.dump(content, js, ensure_ascii=False, indent=4)
        elif mode == 'r':
            result = json.load(js)
            return result