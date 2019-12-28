# | Created by Ar4ikov
# | Время: 28.12.2019 - 15:28

from unittest import TestCase, main
from importlib import import_module


class VkBotLight_Tests(TestCase):
    ACCESS_TOKEN = "your-test-token"
    SECRET_KEY = "your-test-secret-key"
    CONFIRMATION_KEY = "your-test-confirm-key"

    def test_import(self):

        try:
            vk = import_module("vkbotlight")
        except ImportError as e:

            vk = None

        self.assertIn("VkBotLight", dir(vk), "You should install VkBotLight lib first.")

    def test_auth(self):

        import vkbotlight as vk

        self.api = vk.VkBotLight(
            access_token=self.ACCESS_TOKEN,
            secret_key=self.SECRET_KEY,
            confirmation_key=self.CONFIRMATION_KEY
        )

        self.assertIsInstance(self.api, vk.VkBotLight)

    def test_api_connection(self):

        import vkbotlight as vk

        self.api = vk.VkBotLight(
            access_token=self.ACCESS_TOKEN,
            secret_key=self.SECRET_KEY,
            confirmation_key=self.CONFIRMATION_KEY
        )

        self.methods = self.api.methods

        response = self.methods.users.get(user_id="160213445")

        self.assertIsInstance(response, dict, "Bad response from API. Check your internet connection or contact admin.")
        self.assertIn("response", response.keys(), "Bad authentication. Check your access token or contact admin.")

    def test_polling_running(self):
        pass


if __name__ == "__main__":
    main()
