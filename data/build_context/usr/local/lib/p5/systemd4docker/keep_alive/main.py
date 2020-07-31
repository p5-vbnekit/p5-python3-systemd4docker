#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys


def _main():
    class _Context(object):
        timeout = +1.2e+2

    def _make_command():
        _arguments = sys.argv
        if 1 < len(_arguments):
            _command, = _arguments[1:]
            return _command
        return None

    if "stdin_subprocess_main" == _make_command():
        def _command_routine():
            import os
            import time
            import threading

            _Context.event = threading.Condition()
            _Context.timeout = +2.0e+0 * _Context.timeout
            _Context.time_barrier = time.monotonic() + _Context.timeout

            def _thread_routine():
                try:
                    _stream = sys.stdin.fileno()
                    while True:
                        _size = len(os.read(_stream, 1024))
                        print(_size, file = sys.stdout)
                        sys.stdout.flush()
                        if not (0 < _size): break
                        with _Context.event:
                            _Context.time_barrier = time.monotonic() + _Context.timeout
                            _Context.event.notify_all()
                finally:
                    with _Context.event:
                        _Context.time_barrier = None
                        _Context.event.notify_all()

            _thread = threading.Thread(target = _thread_routine, daemon = True)
            _thread.start()

            with _Context.event:
                while _thread.is_alive():
                    if _Context.time_barrier is None: break
                    _time = time.monotonic()
                    if not (_Context.time_barrier > _time): raise TimeoutError()
                    _Context.event.wait(timeout = _Context.time_barrier - _time)

    else:
        def _command_routine():
            import time
            import signal
            import asyncio
            import os.path
            import traceback
            import subprocess

            _Context.tasks = []
            _Context.loop = None
            _Context.event = None
            _Context.condition = True
            _Context.main_task = None
            _Context.stdin_task = None
            _Context.time_barrier = None

            def _make_signal_codes():
                class _Result(object):
                    def __init__(self):
                        super().__init__()
                        self.SIGTERM = None
                        self.SIGUSR1 = None

                _result = _Result()
                try: _result.SIGTERM = signal.SIGTERM
                except AttributeError: pass
                try: _result.SIGUSR1 = signal.SIGUSR1
                except AttributeError: pass
                return _result

            _Context.signal_codes = _make_signal_codes()

            def _print_message(message):
                print(message, file = sys.stderr)
                sys.stderr.flush()

            async def _coroutine():
                _Context.event = asyncio.Condition()
                _Context.time_barrier = time.monotonic() + _Context.timeout

                try:
                    async def _sigusr1_coroutine():
                        async with _Context.event:
                            _Context.time_barrier = time.monotonic() + _Context.timeout
                            _Context.event.notify_all()

                    async def _sigterm_coroutine():
                        _print_message("SIGTERM received")
                        async with _Context.event:
                            _Context.condition = False
                            _Context.event.notify_all()

                    def _add_signal_handler(key, coroutine):
                        def _routine(): _Context.tasks.append(_Context.loop.create_task(coroutine()))
                        try: _Context.loop.add_signal_handler(sig = key, callback = lambda: _Context.loop.call_soon_threadsafe(_routine))
                        except NotImplementedError:
                            traceback.print_exc(file = sys.stderr)
                            sys.stderr.flush()

                    if _Context.signal_codes.SIGUSR1 is None: _print_message("SIGUSR1 is not supported")
                    else: _add_signal_handler(key = _Context.signal_codes.SIGUSR1, coroutine = _sigusr1_coroutine)
                    if _Context.signal_codes.SIGTERM is None: _print_message("SIGTERM is not supported")
                    else: _add_signal_handler(key = _Context.signal_codes.SIGTERM, coroutine = _sigterm_coroutine)

                    async def _stdin_coroutine():
                        _subprocess = await asyncio.create_subprocess_exec(
                            sys.executable, os.path.abspath(__file__), "stdin_subprocess_main",
                            stdin = None, stdout = subprocess.PIPE, stderr = subprocess.DEVNULL
                        )

                        try:
                            _subprocess_task = _Context.loop.create_task(_subprocess.wait())
                            try:
                                while not _subprocess_task.done():
                                    _size = int(await _subprocess.stdout.readline())
                                    if not (0 < _size): break
                                    async with _Context.event:
                                        _Context.time_barrier = time.monotonic() + _Context.timeout
                                        _Context.event.notify_all()
                            finally:
                                if not _subprocess_task.done(): _subprocess_task.cancel()
                                await asyncio.gather(_subprocess_task, return_exceptions = True)

                        finally:
                            _subprocess.terminate()
                            await _subprocess.wait()

                    _Context.stdin_task = _Context.loop.create_task(_stdin_coroutine())
                    _Context.tasks.append(_Context.stdin_task)

                    async def _main_coroutine():
                        async with _Context.event:
                            while _Context.condition:
                                _time = time.monotonic()
                                try:
                                    if not (_Context.time_barrier > _time): raise asyncio.TimeoutError()
                                    await asyncio.wait_for(_Context.event.wait(), timeout = _Context.time_barrier - _time)
                                except asyncio.TimeoutError:
                                    _print_message("timeout occurred, shutting down the system")
                                    subprocess.check_call(("systemd-run", "--on-active=5", "systemctl", "poweroff"))
                                    raise
                        _print_message("exiting without shutdown")

                    _Context.main_task = _Context.loop.create_task(_main_coroutine())
                    _Context.tasks.append(_Context.main_task)

                    async def _manage_tasks():
                        await asyncio.wait(_Context.tasks, return_when = asyncio.FIRST_COMPLETED)
                        _done = tuple([_task for _task in _Context.tasks if _task.done()])
                        for _task in _done: _Context.tasks.remove(_task)
                        await asyncio.gather(*_done, return_exceptions = True)

                    while not _Context.main_task.done(): await _manage_tasks()
                    await _Context.main_task

                finally:
                    if not ((_Context.stdin_task is None) or _Context.stdin_task.done()): _Context.stdin_task.cancel()
                    await asyncio.gather(*_Context.tasks, return_exceptions = True)

            if "win32" == sys.platform: asyncio.set_event_loop(asyncio.ProactorEventLoop())

            _Context.loop = asyncio.get_event_loop()
            _Context.loop.run_until_complete(_coroutine())

    _command_routine()


if "__main__" == __name__: _main()
