from .errors import MessageParsingError

class MessageRequest:
    def __init__(self, request: dict) -> None:
        try:
            self.args : str = request["args"]
            self.command : str = request["command"]
        except KeyError as e:
            raise MessageParsingError(f"Request parsing error: {str(e)}")
