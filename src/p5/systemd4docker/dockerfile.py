#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

from . import __file__ as _this_module_absolute_path
_this_module_package_sequence = str(__package__).split(".")
_this_module_level = "../" * len(_this_module_package_sequence)


def _make_path():
    _path = _this_module_absolute_path
    if not isinstance(_path, str): raise TypeError("non-empty string expected")
    if not _path: raise ValueError("non-empty string expected")
    _prefix_path = sys.exec_prefix
    if not isinstance(_prefix_path, str): raise TypeError("non-empty string expected")
    if not _prefix_path: raise ValueError("non-empty string expected")
    _path = os.path.realpath(os.path.normpath(os.path.abspath(_path)))
    _prefix_path = os.path.realpath(os.path.normpath(os.path.abspath(_prefix_path)))
    _common_path = os.path.commonpath((_path, _prefix_path))
    if len(_common_path) < len(_prefix_path): return os.path.realpath(os.path.normpath(os.path.join(os.path.dirname(_path), _this_module_level, "../data/Dockerfile")))
    return os.path.realpath(os.path.normpath(os.path.join(_prefix_path, "share", "/".join(_this_module_package_sequence), "Dockerfile")))


path = _make_path()
