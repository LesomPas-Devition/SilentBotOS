
n = "\n"

class LogWrite:
    _i = None

    def __new__(cls, *args, **kwargs):
        if cls._i is None:
            cls._i = super().__new__(cls)
        return cls._i

    def __init__(atEvent, returnEvent=None, error=None):
        self.atEvent = self.atEvent
        self.returnEvent = returnEvent
        self.error = error

        if returnEvent is None:
            if self.error is None:
                logSentNormal()
                return
            logSentError()
        else:
            if self.error is None:
                logReplyNormal()
            logReplyError

    def logSentNormal(self):
        with open("./log.txt", "a") as l:
            l.write(f"sent: [{self.atEvent['time']}] Normal GOI: {self.atEvent['msgGOI']} MOI: {self.atEvent['msgMOI']}" + n)
            l.write(f"      Command: {self.atEvent['content']['command']} Params: {self.atEvent['content']['params']}" + n)

    def logSentError(self):
        with open("./log.txt", "a") as l:
            l.write(f"sent: [{self.atEvent['time']}] Error[{self.error}] GOI: {self.atEvent['msgGOI']} MOI: {self.atEvent['msgMOI']}" + n)
            l.write(f"      Information: {atEvent['message'].content}" + n)

    def logReplyNormal(self):
        with open("./log.txt", "a") as l:
            l.write(f"sent: [{self.returnEvent['time']}] Normal GOI: {self.atEvent['msgGOI']} MOI: {self.atEvent['msgMOI']}" + n)
            l.write(f"      Command: {self.atEvent['content']['command']} Params: {self.atEvent['content']['params']}" + n)

    def logReplyError(self):
        with open("./log.txt", "a") as l:
            errorlist = ""
            for i in self.error:
                errorlist += f"{i} "
            l.write(f"sent: [{self.atEvent['time']}] Error[{errorlist}]" + n)