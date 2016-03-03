"""Configuration loading tests"""
from contextlib import contextmanager
from json import dumps
from os import environ
from tempfile import NamedTemporaryFile

from hamcrest import (
    assert_that,
    empty,
    equal_to,
    is_,
    none,
)

from microcosm.loaders import (
    get_config_filename,
    load_from_json_file,
    load_from_python_file,
)
from microcosm.metadata import Metadata


@contextmanager
def envvar(key, value):
    """
    Temporarily set an environment variable.

    """
    old_value = environ.get(key)
    environ[key] = value
    yield
    if old_value is None:
        del environ[key]
    else:
        environ[key] = value


@contextmanager
def configfile(data):
    """
    Temporarily create a temporary file.

    """
    configfile_ = NamedTemporaryFile()
    configfile_.write(data)
    configfile_.flush()
    yield configfile_


def test_get_config_filename_not_set():
    """
    If the envvar is not set, not filename is returned.

    """
    metadata = Metadata("foo-bar")
    config_filename = get_config_filename(metadata)
    assert_that(config_filename, is_(none()))


def test_get_config_filename():
    """
    If the envvar is not set, it is used as the filename.

    """
    metadata = Metadata("foo-bar")
    with envvar("FOO_BAR_SETTINGS", "/tmp/foo-bar.conf"):
        config_filename = get_config_filename(metadata)
        assert_that(config_filename, is_(equal_to("/tmp/foo-bar.conf")))


def test_load_from_json_file():
    """
    Return configuration from a json file.

    """
    metadata = Metadata("foo-bar")
    with configfile(dumps(dict(foo="bar"))) as configfile_:
        with envvar("FOO_BAR_SETTINGS", configfile_.name):
            config = load_from_json_file(metadata)
            assert_that(config.foo, is_(equal_to("bar")))


def test_load_from_json_file_not_set():
    """
    Return empty configuration if json file is not defined.

    """
    metadata = Metadata("foo-bar")
    config = load_from_json_file(metadata)
    assert_that(config, is_(empty()))


def test_load_from_python_file():
    """
    Return configuration from a python file.

    """
    metadata = Metadata("foo-bar")
    with configfile("foo='bar'") as configfile_:
        with envvar("FOO_BAR_SETTINGS", configfile_.name):
            config = load_from_python_file(metadata)
            assert_that(config.foo, is_(equal_to("bar")))


def test_load_from_python_file_not_set():
    """
    Return empty configuration if python file is not defined.

    """
    metadata = Metadata("foo-bar")
    config = load_from_python_file(metadata)
    assert_that(config, is_(empty()))