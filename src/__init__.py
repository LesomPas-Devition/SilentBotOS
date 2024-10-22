
from datetime import datetime
from typing import TypedDict
from enum import Enum
from commandsLst import *

def time_conversion(isoTime):

    dt = datetime.fromisoformat(isoTime)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def UpdateDict(my_dict, key, value):
    if key in my_dict:
        my_dict[key].add(value)
    else:
        my_dict[key] = {value}


class Command(TypedDict):
    name: str
    params: list[int]
    processalControl: bool
    # function: Callable
    of: None | str

class Commands(Enum):
    cello: Command = {"name": "cello", "params": [0], \
                        "processalControl": False, "function": DRVCommands.cello, "of": None}

    repeat: Command = {"name": "repeat", "params": [1], \
                         "processalControl": False, "function": NormalCommands.repeat, "of": None}

    help: Command = {"name": "help", "params": [0], \
                       "processalControl": False, "function": DRVCommands.userhelp, "of": None}

    sign: Command = {"name": "sign", "params": [0, 1], \
                       "processalControl": False, "function": SignCommands.sign, "of": None}

    enroll: Command = {"name": "enroll", "params": [0], \
                         "processalControl": False, "function": SignCommands.enroll, "of": None}

    rename: Command = {"name": "rename", "params": [1], \
                         "processalControl": False, "function": SignCommands.rename, "of": None}

    count: Command = {"name": "count", "params": [0, 1], \
                      "processalControl": 2.5, "function": DirectedCommands.count, "of": None}

    lessen: Command = {"name": "lessen", "params": [0], \
                       "processalControl": False, "function": DirectedCommands.lessen, "of": "count"}

    switching: Command = {"name": "switching", "params": [1], \
                          "processalControl": False, "function": SystemCommands.switching, "of": None}

    AAPs: Command = {"name": "AAPs", "params": [0], \
                     "processalControl": False, "function": SystemCommands.allAvailableProcesses, "of": None}

    DriftBottle: Command = {"name": "DriftBottle", "params": [1, 2], \
                     "processalControl": False, "function": DriftBottleCommands.main, "of": None}

    漂流瓶: Command = {"name": "漂流瓶", "params": [1, 2], \
                     "processalControl": False, "function": DriftBottleCommands.main, "of": None}

commandnames = [i.value["name"] for i in Commands]
IsAdmin = SignCommands._isAdmin
