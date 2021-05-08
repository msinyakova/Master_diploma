def parsing(string):
    words = list()
    elem = ''
    for char in string:
        if char != '_':
            elem += char
        else:
            words.append(elem)
            elem = ''
    words.append(elem)
    return words


class Tree:
    def __init__(self, value_, next_=None):
        self.value = value_
        self.next = next_

    def __repr__(self):
        return self.value.elem

    def __str__(self):
        return self.value.elem


class MyTime:
    def __init__(self, string=''):
        self.elem = str(string)
        self.list = parsing(str(string)).copy()

    def __add__(self, string):
        if str(string) == "":
            return self
        self.elem += ('_' + str(string))
        self.list.extend(parsing(str(string)))
        return self

    def __getitem__(self, key):
        if type(key) == int:
            return self.list[key]
        if type(key) == slice:
            result = ""
            start = 0 if key.start is None else key.start
            stop = len(self.list) if key.stop is None else key.stop
            step = 1 if key.step is None else key.step
            flag = False
            while start < stop:
                if flag:
                    result += '_'
                result += self.list[start]
                start += step
                flag = True
            return result

    def __str__(self):
        return self.elem

    def __repr__(self):
        return self.elem

    def __call__(self):
        return self.elem

    def __eq__(self, string):
        if type(string) == str:
            return self.elem == string
        return self.elem == string.elem

    def __ne__(self, string):
        return not (self.__eq__(string))
