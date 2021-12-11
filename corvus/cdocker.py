import docker
from docker.errors import ImageNotFound


def images_exists(name: str, tag: str) -> bool:
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
