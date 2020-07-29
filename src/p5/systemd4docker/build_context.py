#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from . install_prefix import path as _install_prefix_path


def _make_path():
    _package = __package__
    if not isinstance(_package, str): raise TypeError("invalid package, non-empty string expected")
    if not _package: raise ValueError("invalid package, non-empty string expected")
    _package = _package.split(".")
    if _install_prefix_path is None: _data_path = os.path.normpath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", *(("..", ) * len(_package)), "data"))
    else: _data_path = os.path.join(_install_prefix_path, "share", os.path.join(*_package))
    return os.path.join(_data_path, "build_context")


path = _make_path()
