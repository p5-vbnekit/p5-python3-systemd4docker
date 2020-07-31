#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os
import sys
import docker
import threading

from p5.systemd4docker.builder import build as _build_image
from p5.systemd4docker.container import make as _make_container
from p5.systemd4docker.keep_alive import execute as _keep_alive_routine
from p5.systemd4docker.log_handler import execute as _execute_log_handler
from p5.systemd4docker.dockerfile import path as _base_image_dockerfile_path
from p5.systemd4docker.build_context import path as _base_image_build_context_path
from p5.systemd4docker.utils import is_csi_escape_sequence_only as _is_csi_escape_sequence_only


def _main():
    def _print_message(message):
        print("{}: {}".format(__file__, message), file = sys.stderr)
        sys.stderr.flush()

    def _make_build_log_delegate(prefix = None):
        def _result(message):
            for _line in message.strip().splitlines():
                _line = _line.strip()
                if _line:
                    if _is_csi_escape_sequence_only(_line):
                        sys.stderr.write(_line)
                        sys.stderr.flush()
                    else:
                        if prefix is None: _print_message(_line)
                        else: _print_message("{}: {}".format(prefix, _line))
        return _result

    def _make_base_image():
        return _build_image(
            docker_options = dict(
                tag = "p5/systemd4docker-debian",
                path = _base_image_build_context_path, dockerfile = _base_image_dockerfile_path,
                rm = True, pull = True, forcerm = True, custom_context = False
            ),
            log_delegate = _make_build_log_delegate(prefix = "base image build")
        )

    _image = _make_base_image()
    _print_message("base image was built: \"{}\"".format(_image))

    def _make_custom_image():
        _data_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        return _build_image(
            docker_options = dict(
                tag = "p5/systemd4docker-detailed_example", buildargs = dict(base_image = _image),
                path = os.path.join(_data_directory, "detailed.build_context"), dockerfile = os.path.join(_data_directory, "detailed.Dockerfile"),
                rm = True, pull = False, forcerm = True, custom_context = False
            ),
            log_delegate = _make_build_log_delegate(prefix = "custom image build")
        )

    _image = _make_custom_image()
    _print_message("custom image was built: \"{}\"".format(_image))
    docker.from_env().images.get(_image).tag("p5/systemd4docker-detailed_example:stable-{}".format(_image))

    _threads = []

    try:
        with _make_container(image = _image, hostname = "systemd4docker-example") as _container:
            _print_message("container was created, status = \"{}\", id = \"{}\"".format(_container.status, _container.id))

            _output_lock = threading.Lock()

            def _make_output_delegate(stream):
                def _delegate(data):
                    with _output_lock: stream.buffer.write(data)
                return _delegate

            def _make_flush_delegate(stream):
                def _delegate():
                    with _output_lock: stream.flush()
                return _delegate

            _output_connections = (
                {
                    "input_generator": _container.attach(logs = True, stream = True, stdout = False, stderr = True),
                    "output_delegate": _make_output_delegate(sys.stderr),
                    "flush_delegate": _make_flush_delegate(sys.stderr)
                },
                {
                    "input_generator": _container.attach(logs = True, stream = True, stdout = True, stderr = False),
                    "output_delegate": _make_output_delegate(sys.stdout),
                    "flush_delegate": _make_flush_delegate(sys.stdout)
                }
            )

            _print_message("container output was attached")

            _container.start()

            _print_message("container was started, status = \"{}\"".format(_container.status))

            def _print_message_with_lock(message):
                with _output_lock: _print_message(message)

            def _make_keep_alive_thread():
                _container_id = _container.id
                _thread = threading.Thread(target = lambda: _keep_alive_routine(_container_id), daemon = False)
                _thread.start()
                return _thread
            _threads.append(_make_keep_alive_thread())
            _print_message_with_lock("keep_alive thread was started")

            def _make_output_thread():
                _thread = threading.Thread(target = lambda: _execute_log_handler(connections = _output_connections), daemon = False)
                _thread.start()
                return _thread

            _threads.append(_make_output_thread())
            _print_message_with_lock("container output thread was started")

            def _is_example_service_enabled():
                return 0 == _container.exec(
                    cmd = "systemctl is-enabled p5-systemd4docker-example.service",
                    tty = False, stdin = False, stdout = True, stderr = True,
                    detach = False, stream = False, socket = False, demux = False,
                    privileged = False, user = "", environment = None, workdir = None
                ).exit_code

            def _exec_and_check(command, expected_return_code = 0):
                _exec_result = _container.exec(
                    cmd = command,
                    tty = False, stdin = False, stdout = True, stderr = True,
                    detach = False, stream = False, socket = False, demux = False,
                    privileged = False, user = "", environment = None, workdir = None
                )
                _exit_code = _exec_result.exit_code
                if expected_return_code != _exit_code:
                    _stream = io.StringIO()
                    print("failed to execute in container: {}".format(command), file = _stream)
                    print("exit code: {}".format(_exit_code), file = _stream)
                    _output = _exec_result.output.decode("utf-8").strip()
                    if _output:
                        print("--- begin of output ---", file = _stream)
                        print(_output, file = _stream)
                        print("--- end of output ---", file = _stream)
                    raise RuntimeError(_stream.getvalue().strip())

            if _is_example_service_enabled():
                _exec_and_check("systemctl start p5-systemd4docker-wait_for-example_service.target")
                _print_message_with_lock("example service was started")

            _exec_and_check("sleep 42")
            _print_message_with_lock("exec: `sleep 42` was finished")

            _container.wait()
            _print_message_with_lock("container was finished, status = \"{}\"".format(_container.status))

    finally:
        _print_message_with_lock("container should be removed automatically")

        def _join_threads():
            for _thread in _threads:
                if _thread.is_alive(): _thread.join()
                _print_message("thread \"{}\" was finished".format(_thread))

        _join_threads()


if "__main__" == __name__: _main()
