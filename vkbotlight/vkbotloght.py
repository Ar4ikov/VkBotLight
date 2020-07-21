# | Created by Ar4ikov
# | Время: 27.12.2019 - 00:43

from requests import Session
from json import loads
from os import path

from vkbotlight.objects import VkBotLight_Emitter, VkBotLight_ApiPool, VkBotLight_Error, \
    VkBotLight_Logger, Final, VkBotLight_PollingType, VkBotLight_Data


# TODO:
#  * Интегрировать в Api обработчик ошибок и обработчик каптчи (не забудь пополнить счет на rucaptcha.com)
#  * Написать юнит-тесты и документацию;

class VkBotLight:
    def __init__(self, access_token, api_version=None, default_timeout=.34):

        self.logging = VkBotLight_Logger("logs")

        # Сессия запросов
        self.name = "VkBotLight-1"
        self.session = Session()

        # Ивент пул, метод пул и полинг пул
        self.polling_thread = type("Thread", (object,), {"is_alive": lambda: False})
        self.event = VkBotLight_Emitter(self)
        self.method_pool = VkBotLight_ApiPool(self, default_timeout=default_timeout)

        self.HEADERS = loads(open(path.join(path.dirname(__file__), "headers.json"), "r").read())

        self.API_URL = Final("https://api.vk.com")
        self.API_VERSION = Final(api_version or "5.103")
        self.ACCESS_TOKEN = Final(access_token)

        with Final(self.make_request("groups.getById")) as token_info:
            if "error" in token_info:
                if token_info["error"]["error_code"] == 100:
                    self.TOKEN_INFO = Final(self.make_request("users.get").get("response")[0]).get()

                else:
                    # TODO: Подумать, почему тут не работает raise в with блоке
                    raise VkBotLight_Error("Failed to authenticate: invalid access_token.")

            else:
                self.TOKEN_INFO = token_info.get("response")[0]

            self.TOKEN_INFO.update({"token_type": "group" if "name" in self.TOKEN_INFO.keys() else "user"})

        self.__version__ = open(path.join(path.dirname(__file__), "version.txt"), "r").read()

        class ApiMethod:
            def __init__(self, method, root):
                self.method = method
                self.root: VkBotLight = root

            def __getattr__(self, item):
                return ApiMethod(f"{self.method}.{item}" if self.method else f"{item}", self.root)

            def __call__(self, *args, **kwargs):
                if args:
                    raise ValueError("Do not use non-named arguments. ")

                method_timeout = None

                if "method_timeout" in kwargs:
                    method_timeout = kwargs.pop("method_timeout")

                method = VkBotLight_ApiPool.VkMethodObject(self.method, method_timeout=method_timeout, **kwargs)
                self.root.method_pool.queue(method)
                return self.root.method_pool.await_for_response(method)

                # return self.root.make_request(self.method, **kwargs)

        self.api_method_cls = ApiMethod

    def __str__(self):
        return f"<{self.__class__.__name__} -> Bot Id: {self.TOKEN_INFO.get('id') or self.TOKEN_INFO.get('group_id')}>"

    def make_request(self, method, **data):
        request_ = f"{str(self.API_URL)}/method/{method}"
        data.update({"access_token": str(self.ACCESS_TOKEN), "v": str(self.API_VERSION)})

        non_error_statement = True

        while non_error_statement:
            response = self.session.post(request_, data=data, headers=self.HEADERS)
            if response.json().get("error"):
                if response.json().get("error_code") == 100:
                    pass

            return response.json()

    @property
    def methods(self):
        return self.api_method_cls("", self)

    def polling(self, polling_type: VkBotLight_PollingType = VkBotLight_PollingType.LONG_POLL, secret_key=None,
                confirmation_key=None, *args, **kwargs):

        if self.TOKEN_INFO["token_type"] == "user":
            raise VkBotLight_Error("Cannot start LongPoll protocol using User Authorization.")

        self.SECRET_KEY = Final(secret_key)
        self.CONFIRMATION_KEY = Final(confirmation_key)

        self.polling_thread = polling_type.value(self, secret_key=self.SECRET_KEY,
                                                 confirmation_key=self.CONFIRMATION_KEY,
                                                 host=kwargs.get("host"), port=kwargs.get("port"))
        self.polling_thread.start()
