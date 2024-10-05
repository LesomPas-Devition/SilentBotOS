
n = "\n"

class LogWrite:
    _i = None

    def __new__(cls, *args, **kwargs):
        if cls._i is None:
            cls._i = super().__new__(cls)
        return cls._i

    def __init__(self, atEvent, returnEvent=None, error=None):
        self.atEvent = atEvent
        self.returnEvent = returnEvent
        self.error = error

        if returnEvent is None:
            if self.error is None:
                self.logSentNormal()
                return
            self.logSentError()
        else:
            if self.error is None:
                self.logReplyNormal()
                return
            self.logReplyError()


    def getEnvironment(self) -> str:
        c2c = "C2C"
        group = "Group"
        Guild = "Guild"

        if self.atEvent["msgGOI"] is None:
            return c2c
        else:
            return group


    def logSentNormal(self):
        if (env := self.getEnvironment()) == "Group":
            first = f"sent: [{self.atEvent['time']}] Normal GOI: {self.atEvent['msgGOI']} MOI: {self.atEvent['msgMOI']}"
        elif env == "C2C":
            first = f"sent: [{self.atEvent['time']}] Normal Env: {env} MOI: {self.atEvent['msgMOI']}"

        second = f"      Command: {self.atEvent['content']['command']} Params: {self.atEvent['content']['params']}"

        with open("./log.txt", "a") as l:
            l.write(first + n)
            l.write(second + n)


    def logSentError(self):
        if (env := self.getEnvironment()) == "Group":
            first = f"sent: [{self.atEvent['time']}] Error[{self.error}] GOI: {self.atEvent['msgGOI']} MOI: {self.atEvent['msgMOI']}"
        elif env == "C2C":
            first = f"sent: [{self.atEvent['time']}] Error[{self.error}] Env: {env} MOI: {self.atEvent['msgMOI']}"

        with open("./log.txt", "a") as l:
            l.write(first + n)
            l.write(f"      Information: {atEvent['message'].content}" + n)


    def logReplyNormal(self):
        with open("./log.txt", "a") as l:
            l.write(f"reply: [{self.returnEvent['time']}] Normal Env: {self.getEnvironment()} MOI: {self.atEvent['msgMOI']}" + n)
            l.write(f"      Information: {self.returnEvent['information']}" + n)


    def logReplyError(self):
        with open("./log.txt", "a") as l:
            errorlist = ""
            for i in self.error:
                errorlist += f"{i} "
            l.write(f"reply: [{self.returnEvent['time']}] Error[{errorlist}]" + n)
            l.write(f"      {self.returnEvent['information']}" + n)
