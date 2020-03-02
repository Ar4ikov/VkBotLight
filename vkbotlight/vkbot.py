# | Created by Ar4ikov
# | Время: 17.02.2020 - 12:17

from vkbotlight import VkBotLight
from vkbotlight import VkBotLight_Keyboard as Keyboard
from vkbotlight import VkBotLight_Priority as Priority
from vkbotlight import VkBotLight_Events as Events
from vkbotlight import VkBotLight_PollingType as PT
from vkbotlight import VkBotLight_Logger as Logger


class VkBot:
    def __init__(self, access_token, v):
        self.api = VkBotLight(access_token, api_version=v)
        self.methods = self.api.methods

        self.callers = []

    @staticmethod
    def get_command_context(text: str, prefix):
        if text.startswith(prefix):
            command, args = text.split()[0][1:], text.split()[:1]
            is_command = True

            return is_command, command, args

        else:
            is_command = False
            return is_command, text.split()

    def command(self, func, command, prefix=None):
        """TODO: подумать"""
        @self.api.event.on(Events.MESSAGE_NEW)
        def message_new(**data):
            context = self.get_command_context(data.object.message.text, prefix)
            if context[0] is True:
                _, cmd, args = context
                if cmd == command:
                    return func(**data)

        # message_new.__name__ = f"{message_new.__name__}.{command}"

        return message_new

    def run(self):
        self.api.polling(polling_type=PT.LONG_POLL)