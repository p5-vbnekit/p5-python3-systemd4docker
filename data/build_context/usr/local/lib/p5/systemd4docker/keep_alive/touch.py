#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import subprocess


def _main():
    _time_barrier = +3.0e+1 + time.monotonic()
    _fifo_path = "/run/p5/systemd4docker/keep_alive.fifo"

    while True:
        if "disabled" == subprocess.run(
            ("systemctl", "is-enabled", "p5-systemd4docker-keep_alive.socket"),
            check = False, stdin = subprocess.DEVNULL, stdout = subprocess.PIPE, stderr = subprocess.DEVNULL
        ).stdout.decode("utf-8").strip(): raise RuntimeError("keep_alive socket disabled")

        if "active" == subprocess.run(
                ("systemctl", "is-active", "p5-systemd4docker-keep_alive.socket"),
                check = False, stdin = subprocess.DEVNULL, stdout = subprocess.PIPE, stderr = subprocess.DEVNULL
        ).stdout.decode("utf-8").strip():
            if not os.path.exists(_fifo_path): raise FileNotFoundError(_fifo_path)
            break

        _time = time.monotonic()
        if not (_time_barrier > _time): return

        time.sleep(min(+5.0e+0, _time_barrier - _time))

    if os.path.isfile(_fifo_path): raise FileNotFoundError("not a file: {}".format(_fifo_path))
    with open(_fifo_path, mode = "r"), open(_fifo_path, mode = "w") as _stream: print(time.monotonic(), file = _stream)

    _time = time.monotonic()
    if _time_barrier > _time: time.sleep(_time_barrier - _time)


if "__main__" == __name__: _main()
