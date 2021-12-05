"""Tests for the corvus package."""

from corvus import misc


## ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ==== ##
def test_get_xxhash():
    expected = 'b06272a3'  # generated by the OS tool `xxhsum -H32`
    actual = misc.get_xxhash32("test-data/lorem-ipsum.txt")

    assert actual == expected
