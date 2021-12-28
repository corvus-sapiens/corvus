"""Miscellaneous utility functions."""

import json
import logging
import os
import shutil
from typing import Dict
from collections import namedtuple
from datetime import datetime as dt

import magic
import xxhash
import requests
from humanfriendly import format_size

from corvus import cmd


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
FileReport = namedtuple("FileReport", [
    "exists",
    "bytes",
    "human",
    "description",
    "mime",
    "created",
    "modified"
])


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
class VersionFlagNotImplemented(Exception):
    """Raised when an executable does not implement the --version flag."""

    def __init__(self, path: str, stderr: str, rc: str):
        self.path = path
        self.stderr = stderr.strip()
        self.rc = rc
        self.message = f"Version flag not implemented: '{path}', return code {rc}) <- {stderr}"
        super().__init__(self.message)


    def __str__(self):
        return self.message


    def __repr__(self):
        return "({}) {}".format(self.__class__.__name__, self.message)


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
ANSI_COLORS = {
    "black": "\u001b[30m",
    "red": "\u001b[31m",
    "green": "\u001b[32m",
    "yellow": "\u001b[33m",
    "blue": "\u001b[34m",
    "magenta": "\u001b[35m",
    "cyan": "\u001b[36m",
    "white": "\u001b[37m",
    "reversed": "\u001b[7m",
    "bold": "\u001b[1m",
    "reset": "\u001b[0m"
}


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
class NotAGitRepository(Exception):
    """Raised when working directory is not a git repo (and neither any of the parents)."""
    def __init__(self, dir_target: str):
        """
        :param dir_target: directory that was expected to be a git repository
        """
        self.dir_target = dir_target
        self.message = "Not a git repository (or any of the parent directories)"
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}: '{self.dir_target}'"

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"({cls_name}) {self.message}: '{self.dir_target}'"


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
class GitUnexpectedError(Exception):
    """Raised when git returns an unexpected error."""
    def __init__(self, error_msg: str, dir_target: str):
        """
        :param error_msg: stderr from git
        :param dir_target: path to the git repository
        """
        self.dir_target = dir_target
        self.message = error_msg
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}: '{self.dir_target}'"

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"({cls_name}) {self.message}: '{self.dir_target}'"


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
class BadConfigurationFile(Exception):
    """Raised when configuration file cannot be parsed as expected."""

    def __init__(self, error_msg: str, dir_target: str):
        """
        :param error_msg: description of the error
        :param dir_target: location of the malformed configuration file
        """
        self.dir_target = dir_target
        self.message = error_msg
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}: '{self.dir_target}'"

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"({cls_name}) {self.message}: '{self.dir_target}'"


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
class MissingConfigurationFile(Exception):
    """Raised when configuration file cannot be found."""

    def __init__(self, error_msg: str, filename: str):
        """
        :param error_msg: description of the error
        """
        self.filename = filename
        self.message = error_msg
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}: '{self.filename}'"

    def __repr__(self):
        cls_name = self.__class__.__name__
        return f"({cls_name}) {self.message}: '{self.filename}'"


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
def current_git_commit(dir_target: str = "") -> Dict[str, str]:
    """
    Using git via a shell fork, extract current branch and commit hashes.

    :returns: a branch and commit hash dict
    :raises: NotAGitRepository
    """
    if dir_target == "":
        dir_target = os.getcwd()

    describe = cmd.get_cmd_output(f"git -C {dir_target} describe --always")
    if not describe["rc"] == 0 and "fatal: not a git repository" in describe["stderr"]:
        raise NotAGitRepository(dir_target)
    if not describe["rc"] == 0:
        raise GitUnexpectedError(error_msg=describe["stderr"], dir_target=dir_target)
    commit = describe["stdout"]

    rev_parse = cmd.get_cmd_output(f"git -C {dir_target} rev-parse --abbrev-ref HEAD")
    if not rev_parse["rc"] == 0 and "fatal: not a git repository" in rev_parse["stderr"]:
        raise NotAGitRepository(dir_target=dir_target)
    if not rev_parse["rc"] == 0:
        raise GitUnexpectedError(error_msg=rev_parse["stderr"], dir_target=dir_target)
    branch = rev_parse["stdout"]

    return {"commit": commit, "branch": branch}


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def log_obj_instantiation(obj, logger: logging.LoggerAdapter, addendum: str = "") -> None:
    """
    Emit a log message with the given logger, reporting a new instance of an object.

    :param obj: instance to base the report on
    :param logger: logger instance
    :param addendum: supplementary string message
    :return: None
    """

    classname = obj.__class__.__name__

    try:
        name = obj.__name__
    except AttributeError:
        name = None

    id_ = id(obj)

    try:
        pid = obj.pid
    except AttributeError:
        logger.debug(f"Class interface lacks the ``pid`` property: '{classname}'")
        pid = None

    logger.info(f"New instance of '{classname}': name={name}, id={id_}, pid={pid}. {addendum}".strip())


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def ascii2qtask_id(ascii: str) -> str:
    return "".join([chr(int(c)) for c in ascii.split("-")])


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def qtask_id2ascii(qtask_id: str, delim: str = "-") -> str:
    return delim.join([str(ord(c)) for c in qtask_id])


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_xxhash32(path: str) -> str:
    """
    Return an xxhash-32 hash digest of file.

    :param path: path to the file
    :return: an 8 ASCII-character wide string
    """
    x = xxhash.xxh32()

    with open(path, "rb") as file:
        contents = file.read()
        x.update(contents)

    return x.hexdigest()


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def discover_config(name: str, logger: logging.LoggerAdapter, use_prefix: bool = False, location: str = "") -> dict:
    """
    Look for a given filename in typical locations and parse it as a JSON file.
    First of all, the function will attempt to look in the directory defined in
    the <PREFIX>_CONFIG env variable, where <PREFIX> is the extensionless `name`.

    :param name: name of the configuration file
    :param logger: a logging.LoggerAdapter instance
    :param use_prefix: replace extension from `name` with .cfg.json
    :param location: look in this directory first
    :return: a dictionary representation of a JSON file
    """
    if use_prefix:
        prefix = os.path.splitext(os.path.basename(name))[0]
        file_name = f"{prefix}.cfg.json"
    else:
        prefix = ""
        file_name = name

    logger.debug(f"Expecting a configuration file with name: '{file_name}'")

    ## Choose valid paths from the following tuple
    locations = filter(
        lambda d: d is not None and os.path.isdir(d),
        (
            location,
            os.environ.get(f"{prefix.upper()}_CONFIG") or "",
            os.path.abspath(os.curdir),
            os.path.expanduser("~"),
            os.path.expanduser(f"~/.local/share/{prefix}"),
            f"/etc/{prefix}"
        )
    )

    ## Look for the file in each valid location
    for location in locations:
        path_config = os.path.join(location, file_name)

        try:
            with open(path_config, encoding="utf-8") as file:
                try:
                    config = json.load(file)
                    logger.info(f"Using configuration file: '{os.path.realpath(path_config)}'")
                    return config
                except Exception as error:
                    err_message = f"Failed to parse configuration file: '{path_config}'"
                    logger.critical(f"{err_message} ({repr(error)}). Aborting.")
                    raise BadConfigurationFile(err_message, path_config) from error
        except IOError:
            logger.debug(f"'{file_name}' not found under: '{location}'; trying next location ...")

    err_message = "Configuration file not found"
    logger.critical(f"{err_message}: '{file_name}'. Aborting.")
    raise MissingConfigurationFile(err_message, file_name)


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def ping_healthchecks(uuid: str, logger: logging.LoggerAdapter, status: str = "", quiet: bool = False) -> None:
    """
    Send an HTTP ping to the `healthchecks.io`.

    :param healthcheck_uuid: healthchecks.io-provided identifier of an API endpoint
    :param status: additional signal, signifying execution outcome
    :param logger: a logging.LoggerAdapter instance
    :param quiet: log only errors
    """

    if status and status not in ("start", "fail"):
        logger.error(f"Received unknown status: '{status}'. Skipping.")
        return

    hc_url = f"https://hc-ping.com/{uuid}{'/' + status if status else ''}"

    try:
        if not quiet:
            logger.info(f"({status.strip('/') or 'OK'}) Sending a heartbeat ping to: '{hc_url}' ...")
        requests.get(url=hc_url, timeout=10)
    except requests.RequestException as error:
        logger.error(f"Ping failed ({error}): '{hc_url}{status}'")


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def purge_dir_contents(target_dir: str) -> None:
    """
    Remove all files (incl. directories and symlinks) under the `target_dir`.

    :param target_dir: the directory to be purged of content
    :return: None
    """
    with os.scandir(target_dir) as entries:
        for entry in entries:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry.path)
            else:
                os.remove(entry.path)


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def colorize(text: str, name: str, bright: bool = False, reverse: bool = False, bold: bool = False) -> str:
    color = ANSI_COLORS[name]

    if bright:
        color = color.replace("m", ";1m")
    if bold:
        color = color + ANSI_COLORS["bold"]
    if reverse:
        color = color + ANSI_COLORS["reversed"]

    reset = ANSI_COLORS["reset"]
    return f"{color}{text}{reset}"


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_bin_version(path: str, logger: logging.LoggerAdapter) -> str:
    """
    Return the 1st stdout line from calling the executable with '--version'.

    :param path: path of the executable binary file to be checked
    :param logger: an instance of logging.LoggerAdapter
    :raises: NoVersionFlagImplemented
    :returns: string, containing the first line of stdout
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Invalid executable path: '{path}'")

    output = cmd.get_cmd_output(f"{path} --version")

    if output["rc"] != 0:
        logger.error(output['stderr'])
        raise VersionFlagNotImplemented(path=path, stderr=output['stderr'], rc=output['rc'])

    version_string = output['stdout'].strip().split("\n")[0]
    logger.info(f"Detected usable {os.path.basename(path)} ({version_string})")

    return version_string


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_file_report(path: str) -> FileReport:
    """Build a comment on a path, including size, other (optional) info and attach a message.
    :param path: path to be analyzed
    :returns: Dict containing information about the file under the `path`
    """
    report = {
        "exists": False,
        "bytes": None,
        "human": None,
        "description": None,
        "mime": None,
        "created": None,
        "modified": None
    }

    if not os.path.isfile(path):
        return FileReport(**report)
    else:
        report["exists"] = True

    status = os.stat(path)

    report["bytes"] = status.st_size
    report["human"] = format_size(report["bytes"])

    ctime = status.st_ctime
    mtime = status.st_mtime

    report["created"] = dt.strftime(dt.fromtimestamp(ctime), "%Y-%m-%d %H:%M:%S")
    report["modified"] = dt.strftime(dt.fromtimestamp(mtime), "%Y-%m-%d %H:%M:%S")

    with open(path, "rb") as file:
        report["description"] = magic.from_buffer(file.read(2048))
        report["mime"] = magic.from_buffer(file.read(2048), mime=True)

    return FileReport(**report)
