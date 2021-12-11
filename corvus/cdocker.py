import docker
from docker.errors import ImageNotFound
from requests.exceptions import HTTPError


def images_exists(name: str, tag: str) -> bool:
    dclient = docker.client.from_env()

    try:
        _ = dclient.images.get(f"{name}:{tag or 'latest'}")
    except ImageNotFound:
        print("not found")
        return False

    return True
