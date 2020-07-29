#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

_csi_escape_sequence_pattern = re.compile(r"^(\x1b\[[0-9;]*m\s*)+$")


def is_csi_escape_sequence_only(data): return not (re.match(_csi_escape_sequence_pattern, data.strip()) is None)
