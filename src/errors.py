class StreamStatsError(Exception):
    pass


class UnsupportedFormatError(StreamStatsError):
    pass


class CliConfigError(StreamStatsError):
    pass


class InvalidEventError(StreamStatsError):
    where = ""

    def __str__(self):
        text = super().__str__()
        return f"{self.where}: {text}" if self.where else text


class InvalidTimestampError(InvalidEventError):
    pass