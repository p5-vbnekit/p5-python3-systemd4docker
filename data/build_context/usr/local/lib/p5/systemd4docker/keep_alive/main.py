#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import time
import signal
import asyncio
import subprocess


def _main():
    def _print_message(message):
        print(message, file = sys.stderr)
        sys.stderr.flush()

    class _Context(object):
        tasks = []
        loop = None
        event = None
        main_task = None
        condition = True
        timeout = +1.2e+2
        time_barrier = None

    async def _coroutine():
        _Context.event = asyncio.Condition()
        _Context.time_barrier = time.monotonic() + _Context.timeout

        try:
            async def _sigusr1_coroutine():
                async with _Context.event:
                    _Context.time_barrier = time.monotonic() + _Context.timeout
                    _Context.event.notify_all()

            async def _sigterm_coroutine():
                async with _Context.event:
                    _print_message("SIGTERM received".format(_Context.timeout))
                    _Context.condition = False
                    _Context.event.notify_all()

            def _add_signal_handler(key, coroutine):
                def _routine(): _Context.tasks.append(_Context.loop.create_task(coroutine()))
                _Context.loop.add_signal_handler(sig = key, callback = lambda: _Context.loop.call_soon_threadsafe(_routine))

            _add_signal_handler(key = signal.SIGUSR1, coroutine = _sigusr1_coroutine)
            _add_signal_handler(key = signal.SIGTERM, coroutine = _sigterm_coroutine)

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
            await asyncio.gather(*_Context.tasks, return_exceptions = True)

    _Context.loop = asyncio.get_event_loop()
    _Context.loop.run_until_complete(_coroutine())


if "__main__" == __name__: _main()
