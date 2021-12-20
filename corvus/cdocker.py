"""Helper functions for the Docker SDK.

REF https://docker-py.readthedocs.io/
"""

__author__ = "Alexander Gorelyshev"
__email__ = "alexander.gorelyshev@pm.me"

import logging

import docker  # type: ignore
from docker.errors import ImageNotFound  # type: ignore


def image_exists(name: str, tag: str, logger: logging.LoggerAdapter = None) -> bool:
    """
    Check if a Docker image with a given `name`:`tag` combination exists.

    :param name: image name
    :param tag: image tag (e.g., version, "latest", etc.)
    :param logger: logging.LoggerAdapter instance
    :return: True if the image exists, False otherwise
    """
    dclient = docker.client.from_env()

    try:
        _ = dclient.images.get(f"{name}:{tag or 'latest'}")
    except ImageNotFound:
        if logger:
            logger.error(f"Docker image not available: '{name}:{tag}'")
        return False

    return True


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def get_image_labels(name: str, tag: str) -> dict:
    """
    Return a dictionary of Docker image labels.

    :param name: image name
    :param tag: image tag
    :return: a dictionary of Docker image labels
    """
    dclient = docker.from_env()
    return dclient.images.get(f"{name}:{tag or 'latest'}").labels
