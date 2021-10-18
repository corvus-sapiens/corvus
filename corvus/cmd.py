"""Wrappers for subprocess calls and associated helper functions."""

__author__ = "Alexander Gorelyshev"
__email__ = "alexander.gorelyshev@pm.me"


import asyncio
import logging
import os
import subprocess
import sys
from typing import Union

import magic  # type: ignore
from humanfriendly import format_size  # type: ignore


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_cmd_output(cmd: str) -> dict:
    """Run a shell command via subprocess and return exit code and stdout/stderr.
    :param cmd: shell command as a string (supports redirects, wildcards, etc.)
    :returns: a dictionary with return code, stdout and stderr
    """
    proc = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        check=True
    )

    return {"rc": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
async def get_cmd_output_async(cmd: str) -> dict:
    """Run an asynchronous shell command and return exit code and stdout/stderr.
    :param cmd: shell command as a string (supports redirects, wildcards, etc.)
    :returns: a dictionary with return code, stdout and stderr
    """
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True
    )

    stdout_b, stderr_b = await proc.communicate()

    stdout = stdout_b.decode("utf-8")
    stderr = stderr_b.decode("utf-8")

    return {"rc": proc.returncode, "stdout": stdout, "stderr": stderr}


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def make_path_comment(path: str, message: str, logger: logging.LoggerAdapter, work_magic: bool = False, caller_funcname: bool = False) -> Union[str, None]:
    """Build a comment on a path, including size, other (optional) info and attach a message.
    :param path: path to be analyzed
    :param message: user-defined message, a report of some sort
    :param logger: logging.LoggerAdapter instance
    :param work_magic: (optional) add a python-magic description of the path [False]
    :param caller_funcname: (optional) get the name of the caller function [False]
    :returns: string comment containing requested bits of info plus the user-defined message
    """
    try:
        size_bytes = os.stat(path).st_size
        size = format_size(size_bytes)
        # size = f"{int(size_bytes / 1024)} kB" if size_bytes >= 1024 else f"{size_bytes} B"

        if work_magic:
            with open(path, "rb") as file:
                description = magic.from_buffer(file.read(2048))

        output = f"{message} ({size}, {description}): '{path}'"

        if caller_funcname:
            caller = sys._getframe(1).f_code.co_name
            output = f"({caller}) " + output if caller_funcname else output

    except Exception as error:
        logger.error(f"{repr(error)}: '{path}'")
        output = ""

    return output


## An alias for backwards-compatibility
get_output_report = make_path_comment
