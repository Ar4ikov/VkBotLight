# | Created by Ar4ikov
# | Время: 27.12.2019 - 00:43

from threading import Thread, main_thread
from flask import Flask, session, jsonify, render_template
from flask import request as fr
import logging
from time import sleep
from requests import Session
from json import loads
from os import path

from vkbotlight.objects import VkBotLight_Emitter, VkBotLight_Data, VkBotLight_ApiPool


# TODO:
#  * Интегрировать в Api обработчик ошибок и обработчик каптчи (не забудь пополнить счет на rucaptcha.com)
#  * Доделать класс для вывода в эммитер бота (проработать структуру, обработать ответ);
#  * Написать юнит-тесты и документацию;
#  * (+) Создать рабочее и удобное клиентское Api для кнопок ботов;
#  * Переделать ООП в районе запуска пулинга (вынести отдельными классами Callback и BotLongPoll, подключать в init)


class VkBotLight(Flask):
    def __init__(self, access_token, secret_key, confirmation_key, api_version=None):
        super().__init__(__name__)

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

        self.log = logging.getLogger("werkzeug")
        self.log.setLevel(logging.ERROR)
        self.log.disabled = True

        # Сессия запросов
        self.name = "VkBotLight-1"
        self.session = Session()

        # Ивент пул, метод пул и полинг пул
        self.app_thread = type("Thread", (object,), {"is_alive": lambda: False})
        self.event = VkBotLight_Emitter(self)
        self.method_pool = VkBotLight_ApiPool(self)

        self.HEADERS = loads(open(path.join(path.dirname(__file__), "headers.json"), "r").read())

        self.API_URL = Final("https://api.vk.com")
        self.API_VERSION = Final(api_version or "5.103")
        self.ACCESS_TOKEN = Final(access_token)
        self.SECRET_KEY = Final(secret_key)
        self.CONFIRMATION_KEY = Final(confirmation_key)

        with Final(self.make_request("groups.getById")) as token_info:
            if "error" in token_info:
                self.TOKEN_INFO = Final(self.make_request("users.get")["response"]).get()
            else:
                self.TOKEN_INFO = token_info

        self.__version__ = open(path.join(path.dirname(__file__), "version.txt"), "r").read()

        class ApiMethod:
            def __init__(self, method, root):
                self.method = method
                self.root: VkBotLight = root

            def __getattr__(self, item):
                return ApiMethod(f"{self.method}.{item}" if self.method else f"{item}", self.root)

            def __call__(self, *args, **kwargs):
                if args:
                    raise ValueError("Do no use non-named arguments. ")

                method = VkBotLight_ApiPool.VkMethodObject(self.method, **kwargs)
                self.root.method_pool.queue(method)
                return self.root.method_pool.await_for_response(method)

                # return self.root.make_request(self.method, **kwargs)

        self.api_method_cls = ApiMethod

    def __str__(self):
        return f"<{self.__class__.__name__} -> Bot Id: None>"

    def make_request(self, method, **data):
        request_ = f"{str(self.API_URL)}/method/{method}"
        data.update({"access_token": str(self.ACCESS_TOKEN), "v": str(self.API_VERSION)})

        response = self.session.post(request_, data=data, headers=self.HEADERS)

        return response.json()

    @property
    def methods(self):
        return self.api_method_cls("", self)

    def polling(self, polling_type=None, *args, **kwargs):
        class PollingRunner(Thread):
            def __init__(self, emitter, *data, **kw_data):
                super().__init__()

                self.emitter = emitter
                self.data = data
                self.kw_data = kw_data

            def run(self):
                return self.emitter(*self.data)

        kwargs.update({"threaded": True, "debug": False, "load_dotenv": False})

        @self.route("/")
        def index():
            return jsonify(str({"status": True, "version": self.__version__}))

        @self.route("/robots.txt")
        def robots():
            return open(path.join(path.dirname(__file__), "robots.txt"), "r").read()

        @self.route("/callback", methods=["GET", "POST"])
        def callback():
            data = fr.args.to_dict() or fr.json or fr.data or fr.form or {}

            if data.get("type") == "confirmation":
                return str(self.CONFIRMATION_KEY)

            if data.get("secret") != str(self.SECRET_KEY):
                return jsonify(str({"status": False, "error": "Invalid secret key!"}))

            _TYPE = data.pop("type")
            PollingRunner(self.event.emit, _TYPE, VkBotLight_Data(_TYPE, **data)).start()

            return "ok"

        # super().run(*args, **kwargs)

        self.app_thread = Thread(name=self.name, target=super().run, args=args, kwargs=kwargs)
        self.app_thread.start()
