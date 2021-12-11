"""Tools for monitoring directories."""
import logging
import time

from corvus.misc import get_xxhash32


def has_stabilized_hash(filename: str, max_seconds: int = -1, logger: logging.LoggerAdapter = None) -> bool:
    """
    Return False unless under `max_seconds` the xxhash digest of the `file` stops changing.
    :param filename: target file
    :param max_seconds: observe hash changes for at most this many seconds
    :param logger: a logging.LoggerAdapter instance (default=None)
    :return: True if hash has stabilized, False otherwise
    """

    old = None
    while max_seconds != 0:
        new = get_xxhash32(filename)

        if new == old:
            if logger:
                logger.info(f"Digest stabilized for file (xxhash32): '{filename}'")
            return True

        if logger:
            logger.debug(f"{filename}: {old} -> {new}")

        old = new
        time.sleep(1)
        max_seconds -= 1

    return False
