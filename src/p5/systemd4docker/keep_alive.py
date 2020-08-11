#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import inspect

from . container import make_client as _make_client


class ExecException(RuntimeError):
    def __init__(self, command, exit_code = None, output = None):
        _stream = io.StringIO()
        print("failed to execute in container: {}".format(command), file = _stream)
        if not (exit_code is None): print("exit code: {}".format(exit_code), file = _stream)
        if not (output is None):
            _output = output.decode("utf-8").strip()
            if _output:
                print("--- begin of output ---", file = _stream)
                print(_output, file = _stream)
                print("--- end of output ---", file = _stream)
        super().__init__(_stream.getvalue().strip())


def is_guest_service_enabled(container):
    _arguments = dict(
        cmd = "sh -c 'systemctl is-enabled p5-systemd4docker-keep_alive.service >/dev/null 2>/dev/null'",
        tty = False, stdin = False, stdout = True, stderr = True,
        detach = False, stream = False, socket = False,
        privileged = False, user = "", environment = None, workdir = None
    )

    if "demux" in inspect.signature(container.client.containers.model.exec_run).parameters: _arguments["demux"] = False
    return 0 == container.exec(**_arguments).exit_code


def execute(container_id):
    _client = _make_client()
    _api = _client.containers.get(container_id)
    _command = "/usr/local/lib/p5/systemd4docker/keep_alive/touch.py"

    _arguments = dict(
        cmd = _command,
        tty = False, stdin = False, stdout = True, stderr = True,
        detach = False, stream = False, socket = False,
        privileged = False, user = "", environment = None, workdir = None
    )

    if "demux" in inspect.signature(_client.containers.model.exec_run).parameters: _arguments["demux"] = False

    while True:
        _exec_result = _api.exec_run(**_arguments)
        _exit_code = _exec_result.exit_code
        if 0 != _exit_code: raise ExecException(command = _command, exit_code = _exit_code, output = _exec_result.output)


communicate = execute
