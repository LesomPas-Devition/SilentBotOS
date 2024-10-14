
from log import *

def clearSign():
    with open("./TodaySign.json", "w") as j:
        l.write("{}")
        LogWrite().clearSign()

def main():
    clearSign()

maim()