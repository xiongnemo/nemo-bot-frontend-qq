from .errors import MessageParsingError

class MessageRequest:
    def __init__(self, request: dict) -> None:
        try:
            self.args: str = str(request.get("args", ""))
            self.command: str = str(request.get("command", ""))
            self.imgs: list = list(request.get("imgs", []))
            self.raw_message = request.get("raw_message", "")
            self.reply_to = request.get("reply_to", None)
            self._message_id = str(
                request.get("message_id")
                or (self.reply_to.get("message_id") if isinstance(self.reply_to, dict) else "")
                or ""
            )
        except Exception as e:
            raise MessageParsingError(f"Request parsing error: {str(e)}")

    @property
    def message_id(self) -> str:
        if isinstance(self.reply_to, dict) and "message_id" in self.reply_to:
            return str(self.reply_to["message_id"])
        return self._message_id

    @message_id.setter
    def message_id(self, value: str) -> None:
        self._message_id = str(value)

