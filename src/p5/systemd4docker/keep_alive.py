#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import docker


def is_guest_service_enabled(container):
    return 0 == container.exec(
        cmd = "sh -c 'systemctl is-enabled p5-systemd4docker-keep_alive.service >/dev/null 2>/dev/null'",
        tty = False, stdin = False, stdout = True, stderr = True,
        detach = False, stream = False, socket = False, demux = False,
        privileged = False, user = "", environment = None, workdir = None
    ).exit_code


def communicate(container_id):
    _api = docker.from_env().containers.get(container_id)
    _command = "/usr/local/lib/p5/systemd4docker/keep_alive/touch.py"
    while True:
        _exec_result = _api.exec_run(
            cmd = _command,
            tty = False, stdin = False, stdout = True, stderr = True,
            detach = False, stream = False, socket = False, demux = False,
            privileged = False, user = "", environment = None, workdir = None
        )
        _exit_code = _exec_result.exit_code
        if 0 != _exit_code:
            _stream = io.StringIO()
            print("failed to execute in container: {}".format(_command), file = _stream)
            print("exit code: {}".format(_exit_code), file = _stream)
            _output = _exec_result.output.decode("utf-8").strip()
            if _output:
                print("--- begin of output ---", file = _stream)
                print(_output, file = _stream)
                print("--- end of output ---", file = _stream)
            raise RuntimeError(_stream.getvalue().strip())
