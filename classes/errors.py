class MessageParsingError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class NemoError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
