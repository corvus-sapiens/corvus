"""Tests for the corvus package."""

import logging

import pytest

from corvus import logs
from corvus import misc


logger = logs.get_colored_logger(scriptname=__file__, level=logging.DEBUG, persist=False)


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
def test_get_xxhash():
    expected = 'b06272a3'  # generated by the OS tool `xxhsum -H32`
    actual = misc.get_xxhash32("tests/lorem-ipsum.txt")

    assert actual == expected


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def test_discover_config_env(monkeypatch):
    monkeypatch.setenv("TEST_CONFIG", "tests")
    expected = {
        "topicA": {"a": 0},
        "topicB": {"b": 1}
    }

    actual = misc.discover_config(name="test", logger=logger)

    assert actual == expected


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def test_discover_config_env_missing(monkeypatch):
    monkeypatch.setenv("TEST_NONE_CONFIG", "tests")

    with pytest.raises(misc.MissingConfigurationFile):
        misc.discover_config(name="test_none", logger=logger)


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def test_discover_config_env_malformed(monkeypatch):
    monkeypatch.setenv("TEST_MALFORMED_CONFIG", "tests")

    with pytest.raises(misc.BadConfigurationFile):
        misc.discover_config(name="test_malformed", logger=logger)


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def test_discover_config_env_empty(monkeypatch):
    monkeypatch.setenv("TEST_EMPTY_CONFIG", "tests")

    with pytest.raises(misc.BadConfigurationFile):
        misc.discover_config(name="test_empty", logger=logger)


## ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- ##
def test_discover_config():
    expected = {
        "topicA": {"a": 0},
        "topicB": {"b": 1}
    }
    actual = misc.discover_config(name="test", logger=logger, dir_="tests")

    assert actual == expected
