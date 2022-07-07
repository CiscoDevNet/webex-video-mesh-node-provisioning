class LoggingFormatter(object):
    def __init__(self, orig_formatter, patterns):
        self.orig_formatter = orig_formatter
        self._patterns = patterns

    def format(self, record):
        msg = self.orig_formatter.format(record)
        for pattern in self._patterns:
            msg = msg.replace(pattern, "*****")
        return msg

    def __getattr__(self, attr):
        return getattr(self.orig_formatter, attr)
