# | Created by Ar4ikov
# | Время: 28.12.2019 - 15:28

from unittest import TestCase, main
from importlib import import_module


class VkBotLight_Tests(TestCase):
    ACCESS_TOKEN = "your_access_token"
    SECRET_KEY = "your_test_secret_key"
    CONFIRMATION_KEY = "your_test_confirm_key",
    CONNECTION = {"host": "localhost", "port": 80}

    def test_import(self):

        try:
            vk = import_module("vkbotlight")
        except ImportError as e:

            vk = None

        self.assertIn("VkBotLight", dir(vk), "You should install VkBotLight lib first.")

    def test_auth(self):

        import vkbotlight as vk

        self.api = vk.VkBotLight(
            access_token=self.ACCESS_TOKEN
        )

        self.assertIsInstance(self.api, vk.VkBotLight)

    def test_api_connection(self):

        import vkbotlight as vk

        self.api = vk.VkBotLight(
            access_token=self.ACCESS_TOKEN
        )

        self.methods = self.api.methods

        response = self.methods.groups.getById()

        self.assertIsInstance(response, dict, "Bad response from API. Check your internet connection or contact admin.")
        self.assertIn("response", response.keys(), "Bad authentication. Check your access token or contact admin.")

    def test_polling_longpoll(self):

        import vkbotlight as vk

        self.api = vk.VkBotLight(
            access_token=self.ACCESS_TOKEN
        )

        methods = self.api.methods

        self.api.polling(polling_type=vk.VkBotLight_PollingType.LONG_POLL, secret_key=self.SECRET_KEY,
                         confirmation_key=self.CONFIRMATION_KEY)

    def test_polling_callback(self):

        import vkbotlight as vk

        self.api = vk.VkBotLight(
            access_token=self.ACCESS_TOKEN
        )

        methods = self.api.methods

        self.api.polling(polling_type=vk.VkBotLight_PollingType.CALLBACK, secret_key=self.SECRET_KEY,
                         confirmation_key=self.CONFIRMATION_KEY, **self.CONNECTION)


if __name__ == "__main__":
    TestCase.run()
