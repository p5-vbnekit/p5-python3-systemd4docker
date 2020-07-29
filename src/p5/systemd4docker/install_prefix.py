#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json


def _make_path():
    _this_package_directory = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
    _json_path = os.path.join(_this_package_directory, "install_prefix.json")
    if not os.path.exists(_json_path): return None
    with open(_json_path, "r") as _stream: _value = json.load(_stream)
    if not isinstance(_value, dict): raise TypeError("dictionary expected")
    _value = _value["path"]
    if not isinstance(_value, str): raise TypeError("non-empty string expected")
    if not _value: raise ValueError("non-empty string expected")
    return os.path.normpath(os.path.join(_this_package_directory, _value, *(("..", ) * len(__package__.split(".")))))


path = _make_path()
