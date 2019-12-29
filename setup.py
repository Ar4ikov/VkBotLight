# | Created by Ar4ikov
# | Время: 27.12.2019 - 22:18

from setuptools import setup
from os import path


class VkBotLight_Setup:
    def __init__(self):
        self.package = "vkbotlight"

        self.__version__ = open(path.join(path.dirname(__file__), "vkbotlight", "version.txt"), "r").read()

    def setup(self):
        setup(
            name="vkbotlight",
            version=self.__version__,
            install_requires=["flask", "requests"],
            packages=[self.package],
            package_data={self.package: self.__version__},
            url="https://github.com/Ar4ikov/VkBotLight",
            license="MIT Licence",
            author="Nikita Archikov",
            author_email="bizy18588@gmail.com",
            description="A VK Wrapper for easily creating your own bots",
            keywords="opensource vk bot vkbot vkapi api vkbotlight vklight vk_bot_light vk_light vk_api vk_bot_api"
        )


VkBotLight_Setup().setup()
