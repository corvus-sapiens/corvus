"""Convenience tools for better logging."""

__author__ = "Alexander Gorelyshev"
__email__ = "alexander.gorelyshev"

import os
import logging
import sys

from datetime import datetime as dt


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
class ColoredFormatter(logging.Formatter):
    """Colors log messages depending on the their logging level.
    REF https://stackoverflow.com/a/14859558"""

    ANSI_YELLOW = "\u001b[33m"
    ANSI_RED = "\u001b[31m"
    ANSI_RESET = "\u001b[0m"

    def __init__(self, fmt: str):
        super().__init__(
            fmt=fmt,
            datefmt="%d-%m-%Y %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        """Override the format function of logging.Formatter to support colour output"""

        ## Save the original format configured by the user when the logger
        ## ...formatter was instantiated
        format_orig = self._style._fmt

        ## Replace the original format with one customized by logging level
        if record.levelno == logging.WARNING:
            self._style._fmt = f"{self.ANSI_YELLOW}{format_orig}{self.ANSI_RESET}"

        if record.levelno in (logging.ERROR, logging.CRITICAL):
            self._style._fmt = f"{self.ANSI_RED}{format_orig}{self.ANSI_RESET}"

        ## Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        ## Restore the original format configured by the user
        self._style._fmt = format_orig

        return result


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_colored_logger(scriptname: str, log_dir: str = "./logs", level=logging.DEBUG, to_stdout: bool = False, persist: bool = True, pid: bool = False) -> logging.LoggerAdapter:
    """Instantiate a logger that colors messages based on their log level.
    :param scriptname: name to be displayed as the origin for log messages
    :param log_dir: where to put log messages in the filesystem
    :param level: minimum level of messages to log (defaults to DEBUG)
    :param to_stdout: redirect messages to stdandatd output regardless of their level
    :param persist: whether to save log messages to the filesystem
    :param pid: whether to output IDs of the processes that generate messages
    :returns: a logging.LoggerAdapter instance
    """
    fmt = "%(asctime)s | %(filename)-20s| line %(lineno)3d: [%(levelname)8s]  %(message)s"
    extra = {}

    if pid:
        fmt = "%(asctime)s | %(filename)-20s| line %(lineno)3d: [%(levelname)8s]  PID %(pid)-7s: %(message)s"
        extra = {"pid": os.getpid()}

    run_id = dt.strftime(dt.now(), "%d%m%Y-%H%M")

    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    logger = logging.getLogger(scriptname)
    logger.setLevel(level)

    logger.handlers = []

    log_name = f"{os.path.splitext(os.path.basename(scriptname))[0]}.{run_id}.log"
    log_path = os.path.join(log_dir, log_name)

    ## Set up a file handler if user requested persistence mode
    if persist:
        formatter = logging.Formatter(fmt, '%d-%m-%Y %H:%M:%S')
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    ## Create a stream handler
    ch = logging.StreamHandler(sys.stdout) if to_stdout else logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(ColoredFormatter(fmt=fmt))
    logger.addHandler(ch)

    adapter = logging.LoggerAdapter(logger, extra)  # SEE https://stackoverflow.com/a/17558764/15786420

    return adapter
