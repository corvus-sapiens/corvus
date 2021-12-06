"""Miscellaneous utility functions."""

import json
import logging
import os
from typing import Dict

import xxhash

from corvus import cmd


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
        return f"({cls_name}) {self.message}: {self.dir_target}"


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
        return f"({cls_name}) {self.message}: {self.dir_target}"

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
def discover_config(name: str, logger: logging.LoggerAdapter, from_prefix: bool = True) -> dict:
    """
    Look for a given filename in typical locations and parse it as a JSON file.
    First of all, the function will attempt to look in the directory defined in
    the <PREFIX>_CONFIG env variable, where <PREFIX> is the extensionless `name`.

    :param name: name of the configuration file
    :param logger: a logging.LoggerAdapter instance
    :param from_prefix: build a config file name by replacing the extension with '.cfg.json'
    :return: a dictionary representation of a JSON file
    """
    if from_prefix:
        prefix = os.path.splitext(os.path.basename(name))[0]
        file_name = f"{prefix}.cfg.json"
    else:
        prefix = ""
        file_name = name

    logger.debug(f"Expecting a configuration file with name: '{file_name}'")

    for location in (
        os.environ.get(f"{prefix.upper()}_CONFIG") or "",
        os.path.abspath(os.curdir),
        os.path.expanduser("~"),
        os.path.expanduser(f"~/.local/share/{prefix}"),
        f"/etc/{prefix}"
    ):

        try:
            path_config = os.path.join(location, file_name)
            with open(path_config, encoding="utf-8") as file:
                try:
                    config = json.load(file)
                    logger.info(f"Using configuration file: '{os.path.realpath(path_config)}'")
                    return config
                except Exception as error:
                    err_message = f"Failed to parse configuration file: '{path_config}'"
                    logger.critical(f"{err_message} ({repr(error)}). Aborting.")
                    raise BadConfigurationFile(err_message, path_config)
        except IOError:
            logger.debug(f"'{file_name}' not found under: '{location}'; trying next location ...")
            pass

    err_message = "Configuration file not found"
    logger.critical(f"{err_message}: '{file_name}'. Aborting.")
    raise MissingConfigurationFile(err_message, file_name)
