"""Tests for the corvus.monitoring package."""

import os
import tempfile
import threading
import time
from datetime import datetime as dt

import pytest

from corvus.monitoring import has_stabilized_hash


def keep_file_changing(filename: str, period: float, cycles: int) -> None:
    for _ in range(0, cycles):
        with open(filename, "w") as file:
            file.write(dt.strftime(dt.now(), "%Y-%m-%d %H:%M:%S.%f"))
        time.sleep(period)


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
@pytest.mark.parametrize("keep_seconds,max_seconds,expected", [
    (2, 3, True),  # enough time to see hash stabilize
    (3, 2, False),  # not enough time to see hash stabilize
    (2, 2, False),  # an edge case
    (3, -1, True),  # test with no limit for waiting time
])
def test_has_stabilized_hash(keep_seconds, max_seconds, expected):
    """
    Mock a file in transit by creating a file and writing to it for a set number of seconds,

    Writes current date with milliseconds to a temporary file every 500 ms in a separate thread.
    :param keep_seconds: how long to keep the file under changes
    :param max_seconds: wait for the hash to stabilize at most this many seconds
    :param expected: the boolean value that the function is supposed to return
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "hashtest.txt")
        open(filename, 'a', encoding="ascii").close()

        thread = threading.Thread(target=keep_file_changing, args=(filename, 0.5, keep_seconds))
        thread.daemon = True
        thread.start()

        actual = has_stabilized_hash(filename=filename, max_seconds=max_seconds)

    assert expected == actual
