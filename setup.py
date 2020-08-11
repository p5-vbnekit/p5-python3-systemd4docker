#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import setuptools
import setuptools.command.build_py


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

    return *_make_common("Dockerfile"), *_make_common("build_context")


class _Generators(object):
    @classmethod
    def get(cls): return (
        cls.__install_prefix(),
    )

    @staticmethod
    def __install_prefix():
        class _Result(object):
            @property
            def path(self): return "p5/systemd4docker/install_prefix.json"

            def __call__(self, command_interface):
                _build_directory = command_interface.get_finalized_command("build_py").build_lib

                _content = json.dumps(dict(path = os.path.relpath(
                    os.path.realpath(os.path.abspath(os.path.normpath(command_interface.get_finalized_command("install_data").install_dir))),
                    os.path.realpath(os.path.abspath(os.path.normpath(command_interface.get_finalized_command("install_lib").install_dir)))
                )))

                with open(os.path.join(_build_directory, self.path), "w") as _stream: print(_content, file = _stream)

        return _Result()


class _Commands(object):
    @staticmethod
    def build_py():
        class _Result(setuptools.command.build_py.build_py):
            def run(self):
                _original_result = super().run()
                for _generator in _Generators.get(): _generator(command_interface = self)
                return _original_result

            def get_outputs(self, *args, **kwargs):
                _original_result = super().get_outputs(*args, **kwargs)
                return (type(_original_result))((*_original_result, *[os.path.join(self.build_lib, _generated.path) for _generated in _Generators.get()]))

        return _Result


setuptools.setup(
    name = "p5.systemd4docker",
    url = "",
    license = "",
    version = "0.0.3",
    author = "p5-vbnekit",
    author_email = "vbnekit@gmail.com",
    package_dir = {"": "src"},
    packages = setuptools.find_namespace_packages(where = "src", include = ("p5.*", )),
    data_files = _make_data_files(),
    cmdclass = {
        "build_py": _Commands.build_py()
    },
    install_requires = ("docker", ),
    setup_requires = ("wheel", ),
    description = ""
)
