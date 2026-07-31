from .errors import MessageParsingError

class MessageContext:
    def __init__(self, context: dict) -> None:
        try:
            self.group_id = context.get("group_id", "")
            self.user_id = context.get("user_id", "")
            self.message_id = context["message_id"]
        except KeyError as e:
            raise MessageParsingError(f"Context parsing error: {str(e)}")

