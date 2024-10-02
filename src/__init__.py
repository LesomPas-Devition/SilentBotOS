
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

class Commands(Enum):
    oscello: Command = {"name": "oscello", "params": [0], \
                        "processalControl": False, "function": DRVCommands.cello, "of": None}

    osrepeat: Command = {"name": "osrepeat", "params": [1], \
                         "processalControl": False, "function": NormalCommands.repeat, "of": None}

    oshelp: Command = {"name": "oshelp", "params": [0], \
                       "processalControl": False, "function": DRVCommands.userhelp, "of": None}

    ossign: Command = {"name": "ossign", "params": [0, 1], \
                       "processalControl": False, "function": SignCommands.sign, "of": None}

    osenroll: Command = {"name": "osenroll", "params": [0], \
                         "processalControl": False, "function": SignCommands.enroll, "of": None}

    osrename: Command = {"name": "osrename", "params": [1], \
                         "processalControl": False, "function": SignCommands.rename, "of": None}

    count: Command = {"name": "count", "params": [0, 1], \
                      "processalControl": 2.5, "function": DirectedCommands.count, "of": None}

    lessen: Command = {"name": "lessen", "params": [0], \
                      "processalControl": False, "function": DirectedCommands.lessen, "of": "count"}

    switching: Command = {"name": "switching", "params": [1], \
                          "processalControl": False, "function": SystemCommands.switching, "of": None}

commandnames = [i.value["name"] for i in Commands]