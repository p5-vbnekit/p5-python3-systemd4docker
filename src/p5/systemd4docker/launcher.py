#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import threading

from . container import make as _make_container
from . keep_alive import execute as _keep_alive_routine
from . log_handler import execute as _execute_log_handler


class Object(object):
    class Strategy(object):
        def __init__(self, created = None, started = None, stopped = None, finished = None):
            super().__init__()
            self.created = created
            self.started = started
            self.stopped = stopped
            self.finished = finished

    class BasicStrategy(Strategy):
        def __init__(self):
            super().__init__()

            class _Context(object):
                threads = []
                output_lock = threading.Lock()

            # noinspection PyUnusedLocal
            def _created(launcher, container):
                def _make_output_delegate(stream):
                    def _delegate(data):
                        with _Context.output_lock: stream.buffer.write(data)

                    return _delegate

                def _make_flush_delegate(stream):
                    def _delegate():
                        with _Context.output_lock: stream.flush()

                    return _delegate

                _output_connections = (
                    {
                        "input_generator": container.attach(logs = True, stream = True, stdout = False, stderr = True),
                        "output_delegate": _make_output_delegate(sys.stderr),
                        "flush_delegate": _make_flush_delegate(sys.stderr)
                    },
                    {
                        "input_generator": container.attach(logs = True, stream = True, stdout = True, stderr = False),
                        "output_delegate": _make_output_delegate(sys.stdout),
                        "flush_delegate": _make_flush_delegate(sys.stdout)
                    }
                )

                def _make_thread():
                    _thread = threading.Thread(target = lambda: _execute_log_handler(connections = _output_connections), daemon = False)
                    _thread.start()
                    return _thread

                _Context.threads.append(_make_thread())

            # noinspection PyUnusedLocal
            def _started(launcher, container):
                def _make_thread():
                    _container_id = container.id
                    def _routine(): _keep_alive_routine(_container_id)
                    _thread = threading.Thread(target = _routine, daemon = False)
                    _thread.start()
                    return _thread
                _Context.threads.append(_make_thread())

            # noinspection PyUnusedLocal
            def _finished(launcher, container):
                for _thread in _Context.threads:
                    if _thread.is_alive(): _thread.join()

            self.created = _created
            self.started = _started
            self.finished = _finished

    def run(self, *args, **kwargs):
        _strategy = self.__make_strategy(source = self.strategy)
        _container = _make_container(*args, **kwargs)

        try:
            with _container:
                if not (_strategy.created is None): _strategy.created(self, _container)

                _container.start()

                if not (_strategy.started is None): _strategy.started(self, _container)

                _container.wait()

                if not (_strategy.stopped is None): _strategy.stopped(self, _container)
        finally:
            if not (_strategy.finished is None): _strategy.finished(self, _container)

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    def __init__(self, strategy = None):
        super().__init__()
        self.strategy = self.__make_strategy(strategy)

    @classmethod
    def __make_strategy(cls, source):
        if source is None: return cls.Strategy()
        try: return cls.Strategy(**source)
        except TypeError: pass
        _strategy = cls.Strategy()
        try: _strategy.created = source.created
        except AttributeError: pass
        try: _strategy.started = source.started
        except AttributeError: pass
        try: _strategy.stopped = source.stopped
        except AttributeError: pass
        try: _strategy.finished = source.finished
        except AttributeError: pass
        return _strategy


def make(*args, **kwargs): return Object(*args, **kwargs)


def run(*args, **kwargs): return make(strategy = Object.BasicStrategy()).run(*args, **kwargs)
