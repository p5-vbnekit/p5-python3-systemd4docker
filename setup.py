#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import setuptools


def _make_data_files():
    _relative_source_root_directory = "data"
    _relative_destination_root_directory = "share/p5/systemd4docker"
    _absolute_this_directory = os.path.realpath(os.path.dirname(os.path.abspath(__file__)))
    _absolute_source_root_directory = os.path.join(_absolute_this_directory, _relative_source_root_directory)

    def _make_common(source):
        _absolute_source_path = os.path.join(_absolute_source_root_directory, source)
        if os.path.isdir(_absolute_source_path):
            _result = []
            for _item, _directories, _files in os.walk(_absolute_source_path):
                _relative_path = os.path.relpath(_item, _absolute_source_root_directory)
                _result.append((os.path.join(_relative_destination_root_directory, _relative_path), tuple([os.path.join(_relative_source_root_directory, _relative_path, _file) for _file in _files])))
            if _result: return tuple(_result)
        _relative_source_path = os.path.relpath(_absolute_source_path, _absolute_source_root_directory)
        return (os.path.join(_relative_destination_root_directory, os.path.dirname(_relative_source_path)), (os.path.join(_relative_source_root_directory, _relative_source_path),)),

    return _make_common("Dockerfile")


setuptools.setup(
    name = "p5.systemd4docker",
    url = "",
    license = "",
    version = "0.0.0",
    author = "p5-vbnekit",
    author_email = "vbnekit@gmail.com",
    package_dir = {"": "src"},
    packages = setuptools.find_namespace_packages(where = "src"),
    data_files = _make_data_files(),
    install_requires = ("docker", ),
    setup_requires = ("wheel", ),
    description = ""
)
