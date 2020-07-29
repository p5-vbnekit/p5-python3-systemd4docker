#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import subprocess


def _main():
    if 0 == subprocess.call(("systemctl", "is-active", "p5-systemd4docker-keep_alive.service"), stdin = subprocess.DEVNULL, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL):
        subprocess.check_call(("systemctl", "kill", "--signal=USR1", "p5-systemd4docker-keep_alive.service"), stdin = subprocess.DEVNULL)
    time.sleep(+3.0e+1)


if "__main__" == __name__: _main()
