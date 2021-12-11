import docker
import pytest

from corvus import cdocker


@pytest.mark.parametrize("name,tag,expected", [
    ("hello-world", "", True),
    ("busybox", "stable-glibc", True)
])
def test_image_exists_true(name, tag, expected):
    dclient = docker.client.from_env()

    ## Run a throwaway container to pull the image if needed
    dclient.containers.run(
        image=f"{name}:{tag or 'latest'}",
        remove=True
    )

    actual = cdocker.images_exists(name, tag)

    assert actual == expected


@pytest.mark.parametrize("name,tag,expected", [
    ("non-existent-image", "1.0.0", False)
])
def test_image_exists_false(name, tag, expected):
    actual = cdocker.images_exists(name, tag)
    assert actual == expected
