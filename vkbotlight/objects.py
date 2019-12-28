# | Created by Ar4ikov
# | Время: 27.12.2019 - 14:15
import datetime
from enum import Enum
from os import path, mkdir
from threading import Thread, main_thread
from time import sleep
from typing import List
from uuid import uuid4 as uuid


class VkBotLight_Thread(Thread):
    def __init__(self, root, **data):
        super().__init__()

        self.root = root

    def check_main_thread(self):
        return self.root.app_thread.is_alive() or main_thread().is_alive()


class VkBotLight_ApiPool(VkBotLight_Thread):
    class VkMethodObject:
        def __init__(self, method, **data):
            self.method: str = method
            self.data = data

            self.uuid = uuid()

            self.__dict__.update({k: v for k, v in self.data.items()})

            self.response = None

        def __str__(self):
            return f"<{self.__class__.__name__} {self.method.upper()} => {self.uuid}>"

        def set_response(self, response: dict):
            if not self.response:
                self.response = response

            return True

    def __init__(self, root, default_timeout=.34):
        super().__init__(root)

        self.name = "VkBotLight_ApiPool-3"
        self.root = root

        self.pool: List[VkBotLight_ApiPool.VkMethodObject] = []
        self.done: List[VkBotLight_ApiPool.VkMethodObject] = []

        self.max_history_length = 50
        self.default_timeout = default_timeout

        self.start()

    def make_done(self, request):
        if len(self.done) > 50:
            self.done.pop()

        self.done.append(request)

        return True

    def queue(self, method: VkMethodObject):

        self.pool.append(method)

        return True

    def get_queue_method(self):
        if self.pool:
            yield self.pool.pop()

        else:
            yield None

    def run(self):
        while True:

            method: VkBotLight_ApiPool.VkMethodObject = next(self.get_queue_method())

            if method:
                response = self.root.make_request(method.method, **method.data)
                method.set_response(response)

                self.make_done(method)

            if not self.check_main_thread():
                return True

            # print(f"{self.name} is alive")
            sleep(self.default_timeout)

    def await_for_response(self, method: VkMethodObject):
        response = None

        while not response:
            list_responses = [x for x in self.done if x.uuid == method.uuid]

            if list_responses:
                response = list_responses[0]

        return response.response


class VkBotLight_Emitter(VkBotLight_Thread):
    def __init__(self, root):
        super().__init__(root)

        self.name = "VkBotLight_Emitter-2"
        self.root = root

        self.events = []
        self.callers = []

        self.start()

    def get_new_event(self):
        if self.events:
            yield self.events.pop()
        else:
            yield None

    def on(self, event):
        def deco(func, **data):
            self.callers.append({"event": event, "func": func, "data": data})

        return deco

    def emit(self, event, data):

        event = [x for x in self.callers if x["event"] == event]

        if event:
            self.events.append([event[0], data])

    def run(self):
        print(" * Starting Emitter Thread...")
        while True:

            event = next(self.get_new_event())

            if event:
                _event, data = event

                _event["func"](data=data)

            if not self.check_main_thread():
                return True

            # print(f"{self.name} is alive")
            sleep(.001)


class VkBotLight_Data:
    def __init__(self, _type, **data):
        self._type: str = _type
        [self.__dict__.update({k: v}) for k, v in data.items() if k != "secret"]

    def __str__(self):
        return f"<{self.__class__.__name__}.{self._type.upper()} Type>"


class VKBotLight_Logger:
    class Types(Enum):
        FUNCTION_LOGGING    = "[LOG]"
        WARNING_LOGGING     = "[WARN]"
        ERROR_LOGGING       = "[ERROR]"
        SYSTEM_LOGGING      = "[SYSTEM]"

    @staticmethod
    def get(e_: Enum):
        return e_.value

    def __init__(self, log_dir):
        self.log_dir = log_dir

        if not path.isdir(self.log_dir):
            mkdir(self.log_dir)

    def log(self, log_type: Types, log_text):
        dt = datetime.datetime.today()
        time_ = str(datetime.datetime.now().time()).split(".")[0]

        with open(f"{self.log_dir}/{dt.year}_{dt.month}_{dt.day}.txt", "a+") as file:
            file.write(f"[{dt.year}-{dt.month}-{dt.day} {time_}] {self.get(log_type)} {log_text}\n")
