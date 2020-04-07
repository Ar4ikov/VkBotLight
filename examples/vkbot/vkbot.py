# | Created by Ar4ikov
# | Время: 07.04.2020 - 23:14
from random import randint

from vkbotlight import VkBot, BotEvents
from vkbotlight import VkBotLight_Events as Vk_E
import vkbotlight as vk

from re import match


class MyBotEvents(BotEvents):
    HELLO_EVENT = "hello_event"
    BYE_EVENT = "bye_event"

    NON_LATIN_SYM_EVENT = "emoji"


class MyBot(VkBot):
    def __init__(self, access_token, v, log_dir):
        super().__init__(access_token, v, log_dir)

    def execute(self):
        """First event handler"""
        @self.create_event_handler(events=[Vk_E.MESSAGE_NEW])
        def my_message_new_handler_1(data):
            if Vk_E(data.event) == Vk_E.MESSAGE_NEW:
                text = data.object.message.text

                if "hello" in text:
                    print("HELLO")
                    return MyBotEvents.HELLO_EVENT

                if "bye" in text:
                    return MyBotEvents.BYE_EVENT

            return None

        """Second event handler"""
        @self.create_event_handler(events=[Vk_E.MESSAGE_NEW])
        def my_message_new_handler_2(data):
            if Vk_E(data.event) == Vk_E.MESSAGE_NEW:
                text = data.object.message.text

                if not match(r"""[a-zA-Z]""", text):
                    return MyBotEvents.NON_LATIN_SYM_EVENT

        """Event executor"""
        @self.event_function(on=MyBotEvents.HELLO_EVENT)
        def hello(data):
            user_id = data.object.message.from_id

            return self.methods.messages.send(
                peer_id=user_id,
                message="Hello there!",
                random_id=randint(0, int(2e20))
            )

        @self.event_function(on=MyBotEvents.BYE_EVENT)
        def bye(data):
            user_id = data.object.message.from_id

            return self.methods.messages.send(
                peer_id=user_id,
                message="Bye-bye!",
                random_id=randint(0, int(2e20))
            )

        @self.event_function(on=MyBotEvents.NON_LATIN_SYM_EVENT)
        def non_latin_sym(data):
            user_id = data.object.message.from_id

            return self.methods.messages.send(
                peer_id=user_id,
                message="You're just sent a non-latin characters. Please, do not send those again)",
                random_id=randint(0, int(2e20))
            )

    def run(self):
        print(vk.__file__)
        super().run()


my_bot = MyBot("token", v="5.103", log_dir="logs")
my_bot.run()
