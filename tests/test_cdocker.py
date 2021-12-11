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
    ("non-existent-image", "1.0.0", False),
    ("busybox", "non-existent-tag", False)
])
def test_image_exists_false(name, tag, expected):
    actual = cdocker.images_exists(name, tag)
    assert actual == expected


def test_get_image_labels():
    expected = {
        "maintainer.email": "alexander.gorelyshev@pm.me",
        "maintainer": "Alexander Gorelyshev",
        "description": "A mock container with nothing but labels in it",
        "software.version": "0.0.1",
        "dockerfile.version": "1",
        "base.image": "scratch"
    }

    dclient = docker.from_env()
    dclient.images.build(
        tag="scratch-labels:latest",
        path="tests",
        dockerfile="scratch-labels.Dockerfile",
        forcerm=True,
        nocache=True
    )

    actual = cdocker.get_image_labels("scratch-labels", "latest")
    assert actual == expected
