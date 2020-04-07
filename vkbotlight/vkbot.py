# | Created by Ar4ikov
# | Время: 17.02.2020 - 12:17
from abc import abstractmethod, ABC
from enum import Enum
from time import sleep
from typing import List, Optional

from vkbotlight import VkBotLight
from vkbotlight import VkBotLight_Keyboard as Keyboard
from vkbotlight import VkBotLight_Priority as Priority
from vkbotlight import VkBotLight_Events as Events
from vkbotlight import VkBotLight_PollingType as PT
from vkbotlight import VkBotLight_Logger as Logger


class CommandEvent(ABC):
    def __init__(self, vk_bot):
        self.vk_bot = vk_bot

    @abstractmethod
    def on_chat_message(self, chat_message):
        """If something - returns True, else returns False"""
        return True

    @abstractmethod
    def on_keyboard_message(self, keyboard_message):
        """If something - returns True, else returns False"""
        return True


class BotEvents(Enum):
    """Describe here your events and use it in your custom event handler"""


class VkBot:
    def __init__(self, access_token, v, log_dir: Optional[str] = None):
        self.api = VkBotLight(access_token, api_version=v)
        self.methods = self.api.methods

        """Command listeners"""
        self.listeners: List[dict] = []

        """Event handlers"""
        self.event_handlers: List[dict] = []
        self.event_functions: List[dict] = []

        """Logger"""
        self.logger = Logger(log_dir or ".")

    def create_event_handler(self, events=None):
        if events is None:
            events = [Events.EVENTS_ALL]

        def deco(func, *args, **kwargs):
            self.event_handlers.append({
                "func": func,
                "args": args,
                "kwargs": kwargs,
                "events": events
            })

        return deco

    def execute(self):
        """Executing handlers will be here. Use this method to describe your custom event handlers in method body"""

    def event_function(self, on):
        def deco(func, *args, **kwargs):
            self.event_functions.append({
                "func": func,
                "args": args,
                "kwargs": kwargs,
                "event": on
            })

        return deco

    @staticmethod
    def get_command_context(text: str, prefix):
        if text.startswith(prefix):
            command, args = text.split()[0][1:], text.split()[:1]
            is_command = True

            return is_command, command, args

        else:
            is_command = False
            return is_command, text.split()

    def command(self, command, prefix="/"):
        def deco(func, *args, **kwargs):
            self.listeners.append({
                "func": func,
                "args": args,
                "kwargs": kwargs,
                "command": command,
                "prefix": prefix
            })

        return deco

    def handle_functions(self):
        """

        Handling functions like command listener

        :return:
        """
        @self.api.event.on(Events.MESSAGE_NEW, priority=Priority.MAIN_PRIORITY)
        def message_new(data):
            """Command Listener"""
            message = data.object.message
            text = message.text

            for listener in self.listeners:
                _command_context = self.get_command_context(text, listener["prefix"])

                if _command_context[0]:
                    if listener["command"] == _command_context[1]:
                        listener["kwargs"].update({"data": data})
                        listener["func"](*listener["args"], **listener["kwargs"])

            return True

        return True

    def run(self):
        self.execute()
        # self.handle_functions()

        @self.api.event.on(Events.EVENTS_ALL, priority=Priority.MAIN_PRIORITY)
        def bot_executing(data):
            handlers = [x for x in self.event_handlers if Events(data.event) in x["events"]]

            if handlers:
                for handler in handlers:
                    event = handler["func"](data)

                    if event:
                        functions = [x for x in self.event_functions if x["event"] == event][::-1]

                        if functions:
                            for f in functions:
                                f["func"](data=data, *f["args"], **f["kwargs"])

        self.api.polling(polling_type=PT.LONG_POLL)
