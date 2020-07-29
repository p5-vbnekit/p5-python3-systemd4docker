#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import threading


class Connection(object):
    def __init__(self, input_generator, output_delegate, flush_delegate = None):
        super().__init__()
        self.flush_delegate = flush_delegate
        self.output_delegate = output_delegate
        self.input_generator = input_generator


def execute(connections):
    def _make_connection(source):
        try:
            input_generator, output_delegate = source["input_generator"], source["output_delegate"]
            try: flush_delegate = source["flush_delegate"]
            except KeyError: flush_delegate = None
        except TypeError:
            try: input_generator, output_delegate, flush_delegate = source
            except ValueError:
                flush_delegate = None
                input_generator, output_delegate = source
            except TypeError:
                try: flush_delegate = source.flush_delegate
                except AttributeError: flush_delegate = None
                input_generator, output_delegate = source.input_generator, source.output_delegate
        return Connection(input_generator = input_generator, output_delegate = output_delegate, flush_delegate = flush_delegate)

    connections = tuple([_make_connection(_connection) for _connection in connections])
    if not connections: return

    class _ThreadContext(object):
        flush_requests = []
        flush_barrier = None
        stop_condition = False
        event = threading.Condition()

    def _make_threads():
        # noinspection PyShadowingNames
        _all_threads = []
        # noinspection PyShadowingNames
        _output_threads = []
        _flush_delegates = {}

        def _make_output_thread(connection):
            _flush_timeout = +1.0e+0
            _input_generator = connection.input_generator
            _output_delegate = connection.output_delegate
            _flush_request = None if (connection.flush_delegate is None) else id(connection)

            def _routine():
                for _message in _input_generator:
                    with _ThreadContext.event:
                        _output_delegate(_message)
                        _ThreadContext.flush_barrier = time.monotonic() + _flush_timeout
                        if not (_flush_request is None): _ThreadContext.flush_requests.append(_flush_request)
                        _ThreadContext.event.notify_all()
                        if _ThreadContext.stop_condition: break

            return threading.Thread(target = _routine, daemon = False)

        for _connection in connections:
            _output_threads.append(_make_output_thread(_connection))
            if not (_connection.flush_delegate is None): _flush_delegates[id(_connection)] = _connection.flush_delegate

        _all_threads.extend(_output_threads)

        if _flush_delegates:
            def _flush_thread_routine():
                _handled_flush_requests = set()
                with _ThreadContext.event:
                    while not _ThreadContext.stop_condition:
                        if _ThreadContext.flush_requests:
                            try:
                                while not _ThreadContext.stop_condition:
                                    if _ThreadContext.flush_barrier is None: break
                                    _timestamp = time.monotonic()
                                    if _timestamp >= _ThreadContext.flush_barrier: break
                                    _ThreadContext.event.wait(_ThreadContext.flush_barrier - _timestamp)
                            finally:
                                while _ThreadContext.flush_requests:
                                    _id = _ThreadContext.flush_requests.pop()
                                    if _id in _handled_flush_requests: continue
                                    _handled_flush_requests.add(_id)
                                    _flush_delegates[_id]()
                                _handled_flush_requests.clear()
                        else: _ThreadContext.event.wait()

            _all_threads.append(threading.Thread(target = _flush_thread_routine, daemon = False))

        return tuple(_all_threads), tuple(_output_threads)

    _all_threads, _output_threads = _make_threads()

    try:
        for _thread in _all_threads: _thread.start()
        for _thread in _output_threads: _thread.join()
    finally:
        with _ThreadContext.event:
            _ThreadContext.stop_condition = True
            _ThreadContext.event.notify_all()
        for _thread in _all_threads:
            if _thread.is_alive(): _thread.join()
