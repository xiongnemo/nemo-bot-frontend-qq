from itertools import zip_longest
from typing import Iterable, Union
from .message_context import MessageContext
from .message_request import MessageRequest
from .errors import MessageParsingError

import requests

class Message:
    def __init__(self, message: dict) -> None:
        try:
            self.frontend = message["frontend"]
            self.context = MessageContext(message["context"])
            self.request = MessageRequest(message["request"])
        except KeyError as e:
            raise MessageParsingError(f"Message parsing error: {str(e)}")

