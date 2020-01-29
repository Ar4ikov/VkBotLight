# | Created by Ar4ikov
# | Время: 27.12.2019 - 14:15
import datetime
from enum import Enum
from json import dumps
from os import path, mkdir
from threading import Thread, main_thread
from time import sleep
from typing import List
from uuid import uuid4 as uuid

from flask import Flask, session, jsonify, render_template
from flask import request as fr
import logging

from vkbotlight.enums import VkBotLight_Events


class PollingTask(Thread):
    def __init__(self, emitter, *data, **kw_data):
        super().__init__()

        self.emitter = emitter
        self.data = data
        self.kw_data = kw_data

    def run(self):
        return self.emitter(*self.data)


class VkBotLight_Callback(Flask):
    def __init__(self, root, secret_key, confirmation_key, host, port):
        self.root = root

        super().__init__(root.name)

        self.root = root

        self.log = logging.getLogger("werkzeug")
        self.log.setLevel(logging.ERROR)
        self.log.disabled = True

        self.SECRET_KEY = Final(secret_key)
        self.CONFIRMATION_KEY = Final(confirmation_key)

        self.HOST = Final(host)
        self.PORT = Final(port)

    # def is_alive(self):
    #     return self.root.polling_thread.is_alive()

    def start(self, *args, **kwargs):

        kwargs.update({"threaded": True, "debug": False, "load_dotenv": False})
        kwargs.update({"host": self.HOST.get(), "port": self.PORT.get()})

        @self.route("/")
        def index():
            return jsonify(str({"status": True, "version": self.root.__version__}))

        @self.route("/robots.txt")
        def robots():
            return open(path.join(path.dirname(__file__), "robots.txt"), "r").read()

        @self.route("/callback", methods=["GET", "POST"])
        def callback():
            data = fr.args.to_dict() or fr.json or fr.data or fr.form or {}

            if data.get("type") == "confirmation":
                return str(self.CONFIRMATION_KEY.get())

            # print(data.get("secret"), self.SECRET_KEY.get())
            if data.get("secret") != str(self.SECRET_KEY.get()):
                return jsonify(str({"status": False, "error": "Invalid secret key!"}))

            _TYPE = data.pop("type")
            PollingTask(self.root.event.emit, _TYPE, VkBotLight_Data(_TYPE, **data)).start()

            return "ok"

        # super().run(*args, **kwargs)

        self.root.polling_thread = Thread(name=self.root.name, target=super().run, args=args, kwargs=kwargs)
        self.root.polling_thread.start()


class VkBotLight_LongPoll(Thread):
    def __init__(self, root, *args, **kwargs):
        super().__init__()

        self.root = root
        self.name = self.root.name

        if self.root.methods.groups.getLongPollSettings(group_id=self.root.TOKEN_INFO["id"]).get("response") \
                ["is_enabled"] is False:
            raise VkBotLight_Error("LongPoll is not enabled in this group.")

    def initialize_parameters(self):
        response: dict = self.root.methods.groups.getLongPollServer(group_id=self.root.TOKEN_INFO["id"]).get("response")

        self.server, self.key, self.ts = response.get("server"), response.get("key"), response.get("ts")

        response.update({"act": "a_check", "mode": 2, "version": 2, "wait": 25})

        return response

    def run(self):
        self.statement = True

        params = self.initialize_parameters()
        server = params.pop("server")

        while self.statement:

            response = self.root.session.post(f"{server}", params=params)
            response_json = response.json()

            params.update({"ts": response_json.get("ts")})
            events = response_json.get("updates")

            if events is None:
                params = self.initialize_parameters()
            else:
                for event in events:
                    _TYPE = event.pop("type")

                    PollingTask(self.root.event.emit, _TYPE, VkBotLight_Data(_TYPE, **event)).start()

            sleep(.001)


class VkBotLight_PollingType(Enum):
    CALLBACK = VkBotLight_Callback
    LONG_POLL = VkBotLight_LongPoll


class VkBotLight_Thread(Thread):
    def __init__(self, root, **data):
        super().__init__()

        self.root = root

    def check_main_thread(self):
        return self.root.polling_thread.is_alive() or main_thread().is_alive()


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

    def on(self, event: VkBotLight_Events):
        def deco(func, **data):
            self.callers.append({"event": event.value, "func": func, "data": data})

        return deco

    def emit(self, event, data):

        event = [x for x in self.callers if x["event"] == event]

        if event:
            self.events.append([event[0], data])

    def run(self):
        # print(" * Starting Emitter Thread...")
        while True:

            event = next(self.get_new_event())

            if event:
                _event, data = event

                _event["func"](data=data)

            if not self.check_main_thread():
                return True

            # print(f"{self.name} is alive")
            sleep(.001)


class VkBotLight_Keyboard:
    class ButtonColors(Enum):
        VK_PRIMARY = "primary"
        VK_SECONDARY = "secondary"
        VK_NEGATIVE = "negative"
        VK_POSITIVE = "positive"

    def __init__(self, one_time=False, inline=False, **data):
        self.app_hash = data.get("hash")
        self.app_id = data.get("app_id")
        self.owner_id = data.get("owner_id")

        self.one_time = one_time
        self.inline = inline
        self.buttons = [[]]

    def append_single(self, button):

        if len(self.buttons[-1]) == 0:
            self.append(button)
            self.add_row()
        else:
            self.add_row()
            self.append(button)

        return True

    def append(self, button):
        self.buttons[-1].append(button)

        return True

    @staticmethod
    def generate_pay_hash(group_id, aid):
        return f"action=transfer-to-group&group_id={group_id}&aid={aid}"

    def text(self, text, color: ButtonColors = ButtonColors.VK_PRIMARY, payload: str = None, returns=True):
        button = {"action": {"type": "text", "payload": payload, "label": text}, "color": color.value}

        self.append(button)

        if returns:
            return button

    def open_link(self, text, link, payload: str = None, returns=True):
        button = {"action": {"type": "open_link", "link": link, "label": text, "payload": payload}}

        self.append(button)

        if returns:
            return button

    def location(self, payload: str = None, returns=True):
        button = {"action": {"type": "location", "payload": payload}}

        self.append_single(button)

        if returns:
            return button

    def vkpay(self, pay_hash: str, payload: str = None, returns=True):
        button = {"action": {"type": "vkpay", "hash": pay_hash, "payload": payload}}

        self.append_single(button)

        if returns:
            return button

    def open_app(self, app_id: int, owner_id: int, app_name: str = None, app_hash: str = "open_app", payload: str = None,
                 returns=True):
        button = {"action": {"type": "open_app", "app_id": app_id, "owner_id": owner_id, "payload": payload,
                             "label": app_name, "hash": app_hash}}

        self.append_single(button)

        if returns:
            return button

    def add_row(self):
        self.buttons.append([])

        return True

    def set_keyboard(self, buttons: list):
        self.buttons = buttons

        return True

    def get(self):
        return dumps({
            "one_time": self.one_time if self.inline is False else False,
            "inline": self.inline,
            "buttons": self.buttons
        }, sort_keys=False, ensure_ascii=False)


class VkBotLight_Data:
    class VkBotLight_DataStruct:
        def __init__(self, **data):
            [self.__dict__.update({k: v}) if not isinstance(v, dict) else self.__dict__.update(
                {k: VkBotLight_Data.VkBotLight_DataStruct(**v)}) for k, v in data.items()]

    def __init__(self, _type, is_method_data=False, **data):
        self._type: str = _type
        self.is_method_data = is_method_data
        [self.__dict__.update({k: v}) if not isinstance(v, dict) else self.__dict__.update(
            {k: VkBotLight_Data.VkBotLight_DataStruct(**v)}) for k, v in data.items() if k != "secret"]

    def __str__(self):
        return f"<{self.__class__.__name__}.{self._type.upper()} {'Method' if self.is_method_data else 'Type'} {self.__dict__}> "


class VkBotLight_Logger:
    class Types(Enum):
        FUNCTION_LOGGING = "[LOG]"
        WARNING_LOGGING = "[WARN]"
        ERROR_LOGGING = "[ERROR]"
        SYSTEM_LOGGING = "[SYSTEM]"

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


class VkBotLight_CaptchaHandler:
    def __init__(self, rucaptcha_key):
        self.rucaptcha_key = rucaptcha_key

    def get_photo(self):
        pass

    def solve_captcha(self):
        pass


class VkBotLight_Error(Exception): ...


class Final:
    def __init__(self, value):
        self.value = value

    def __setattr__(self, key, value):
        if key in self.__dict__:
            raise AttributeError("Cannot edit a Final.")
        else:
            self.__dict__.update({key: value})

            return None

    def __str__(self):
        return self.value

    def __enter__(self):
        return self.value

    def __exit__(self, *_):
        return True

    def get(self):
        return self.value
