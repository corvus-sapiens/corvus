"""Miscellaneous utility functions."""

import os
import logging
import xxhash

from typing import Dict

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


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
def current_git_commit(dir_target: str = "") -> Dict[str, str]:
    """
    Using git via a shell fork, extract current branch and commit hash.
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
def get_xxhash(path: str) -> str:
    x = xxhash.xxh32()

    with open(path, "rb") as file:
        contents = file.read()
        x.update(contents)

    return x.hexdigest()
