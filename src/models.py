from datetime import datetime, timezone

from .errors import InvalidEventError, InvalidTimestampError

levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
fields = ("timestamp", "level", "source", "message")


class Markdown:
    """Одна записаь из файла(событие)"""

    def __init__(self, markd):
        for name in fields:
            if markd.get(name) is None:
                raise InvalidEventError(f"missing field '{name}'")
        raw = markd["timestamp"]
        if not isinstance(raw, str):
            raise InvalidTimestampError("timestamp must be a string")

        try:
            ts = datetime.fromisoformat(raw.strip())
        except ValueError:
            raise InvalidTimestampError(f"invalid timestamp {raw!r}") from None
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        self.timestamp = ts

        level = markd["level"]
        if not isinstance(level, str) or level.strip().upper() not in levels:
            raise InvalidEventError(f"unknown level {level!r}")
        self.level = level.strip().upper()

        source = markd["source"]
        if not isinstance(source, str) or not source.strip():
            raise InvalidEventError("source must be a non-empty string")
        self.source = source

        message = markd["message"]
        if not isinstance(message, str):
            raise InvalidEventError("message must be a string")
        self.message = message
