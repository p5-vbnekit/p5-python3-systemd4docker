#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import copy
import time
import docker
import threading


class Defaults(object):
    tmpfs = {"/run": "", "/run/lock": ""}

    environment = {"container": "docker"}

    volumes = {
        "/dev/hugepages": {"bind": "/dev/hugepages", "mode": "ro"},
        "/sys/fs/cgroup": {"bind": "/sys/fs/cgroup", "mode": "ro"}
    }


def run(image, **kwargs):
    _options = copy.deepcopy(kwargs)

    def _fix_option(name, defaults):
        if name in _options:
            _option = _options[name] = dict(_options[name])
            for _key in defaults:
                if not (_key in _option): _option[_key] = copy.deepcopy(defaults[_key])
        else: _options[name] = copy.deepcopy(defaults)

    _fix_option("tmpfs", Defaults.tmpfs)
    _fix_option("environment", Defaults.environment)
    _fix_option("volumes", Defaults.volumes)

    _container = docker.from_env().containers.run(
        image = image, command = None,
        tty = True, stdout = False, stderr = False,
        remove = True, detach = True, auto_remove = True,
        **_options
    )

    try:
        _flush_timeout = +1.0e+0

        class _ThreadContext(object):
            def __init__(self):
                super().__init__()
                self.flush_barrier = None
                self.event = threading.Condition()

        _thread_context = _ThreadContext()

        def _make_stream_thread(input_stream, output_stream):
            def _routine():
                for _message in input_stream:
                    with _thread_context.event:
                        output_stream.write(_message)
                        _thread_context.flush_barrier = time.monotonic() + _flush_timeout
                        _thread_context.event.notify_all()
            return threading.Thread(target = _routine, daemon = True)

        def _flush_thread_routine():
            with _thread_context.event:
                while True:
                    if _thread_context.flush_barrier is None: _thread_context.event.wait(_flush_timeout)
                    if _thread_context.flush_barrier is None: continue
                    if _thread_context.flush_barrier is False: break
                    _timestamp = time.monotonic()
                    if _thread_context.flush_barrier > _timestamp: _thread_context.event.wait(_thread_context.flush_barrier - _timestamp)
                    if _thread_context.flush_barrier is False: break
                    if _thread_context.flush_barrier is None: continue
                    if _thread_context.flush_barrier > time.monotonic(): continue
                    _thread_context.flush_barrier = None
                    sys.stdout.flush()
                    sys.stderr.flush()

        _threads = (
            _make_stream_thread(input_stream = _container.logs(stream = True, stdout = True, stderr = False), output_stream = sys.stdout.buffer),
            _make_stream_thread(input_stream = _container.logs(stream = True, stdout = False, stderr = True), output_stream = sys.stderr.buffer),
            threading.Thread(target = _flush_thread_routine, daemon = False)
        )

        try:
            for _thread in _threads: _thread.start()
            _container.wait()
        finally:
            _container.stop()
            with _thread_context.event:
                _thread_context.flush_barrier = False
                _thread_context.event.notify_all()
            for _thread in _threads: _thread.join()

    finally:
        # noinspection PyBroadException
        try:
            _container.stop()
            _container.wait()
        except BaseException: pass

