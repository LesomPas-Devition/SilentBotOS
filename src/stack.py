
class Stack:

    def __init__(self, data=None):
        if data is None:
            self.data = []
            return

        if type(data) != list:
            raise TypeError('The type should is list')

        self.data = data

    def push(self, data):
        self.data.append(data)

    def pop(self):
        return self.data.pop()

    def empty(self):
        if self.data == []:
            return True
        return False