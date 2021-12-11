"""Helper functions for the Docker SDK.

REF https://docker-py.readthedocs.io/
"""

__author__ = "Alexander Gorelyshev"
__email__ = "alexander.gorelyshev@pm.me"


import docker  # type: ignore
from docker.errors import ImageNotFound  # type: ignore


def image_exists(name: str, tag: str) -> bool:
    """
    Check if a Docker image with a given `name`:`tag` combination exists.

    :param name: image name
    :param tag: image tag (e.g., version, "latest", etc.)
    :return: True if the image exists, false otherwise
    """
    dclient = docker.client.from_env()

    try:
        _ = dclient.images.get(f"{name}:{tag or 'latest'}")
    except ImageNotFound:
        print("not found")
        return False

    return True


def get_image_labels(name: str, tag: str) -> dict:
    """
    Return a dictionary of Docker image labels.

    :param name: image name
    :param tag: image tag
    :return: a dictionary of Docker image labels
    """
    dclient = docker.from_env()
    return dclient.images.get(f"{name}:{tag or 'latest'}").labels
