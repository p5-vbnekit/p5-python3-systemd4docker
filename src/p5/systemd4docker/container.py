#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import docker
import docker.errors


class Object(object):
    class Defaults(object):
        tmpfs = {"/run": "", "/run/lock": ""}

        environment = {"container": "docker"}

        volumes = {
            "/dev/hugepages": {"bind": "/dev/hugepages", "mode": "ro"},
            "/sys/fs/cgroup": {"bind": "/sys/fs/cgroup", "mode": "ro"}
        }

        remove = True

        stop_signal = "SIGINT"

    @property
    def id(self): return self.__manipulate(lambda _api: _api.id)

    @property
    def image(self): return self.__manipulate(lambda _api: _api.image)

    @property
    def labels(self): return self.__manipulate(lambda _api: _api.labels)

    @property
    def name(self): return self.__manipulate(lambda _api: _api.name)

    @property
    def status(self): return self.__manipulate(lambda _api: _api.status)

    def wait(self, *args, **kwargs): return self.__manipulate(lambda _api: _api.wait(*args, **kwargs))
    def exec(self, *args, **kwargs): return self.__manipulate(lambda _api: _api.exec_run(*args, **kwargs))
    def attach(self, *args, **kwargs): return self.__manipulate(lambda _api: _api.attach(*args, **kwargs))
    def start(self, *args, **kwargs): return self.__manipulate(lambda _api: _api.start(*args, **kwargs))
    def stop(self, *args, **kwargs): return self.__manipulate(lambda _api: _api.stop(*args, **kwargs))
    def restart(self, *args, **kwargs): return self.__manipulate(lambda _api: _api.restart(*args, **kwargs))

    def __init__(self, image, **kwargs):
        super().__init__()

        if not isinstance(image, str): raise TypeError("invalid image, non-empty string expected")
        if not image: raise ValueError("invalid image, non-empty string expected")

        _options = dict(**copy.deepcopy(kwargs))

        try:
            _remove = _options.pop("remove")
            if not isinstance(_remove, bool): raise TypeError("invalid remove option, boolean expected")
        except KeyError:  _remove = self.Defaults.remove

        if "stream" in _options: raise ValueError("unexpected option: stream")
        if "stdout" in _options: raise ValueError("unexpected option: stdout")
        if "stderr" in _options: raise ValueError("unexpected option: stderr")

        def _fix_option(name, defaults):
            if name in _options:
                _option = _options[name] = dict(_options[name])
                for _key in defaults:
                    if not (_key in _option): _option[_key] = copy.deepcopy(defaults[_key])
            else: _options[name] = copy.deepcopy(defaults)

        _fix_option("tmpfs", self.Defaults.tmpfs)
        _fix_option("environment", self.Defaults.environment)
        _fix_option("volumes", self.Defaults.volumes)

        if not ("stop_signal" in _options): _options["stop_signal"] = self.Defaults.stop_signal

        _options = dict(image = image, command = None, tty = True, detach = True, auto_remove = _remove, **_options)

        self.__api = None
        self.__entered = 0
        self.__options = _options

    def __enter__(self):
        self.__entered += 1
        if 1 < self.__entered: return
        self.__api = docker.from_env().containers.create(**self.__options)
        return self

    def __exit__(self, exception_type, exception_instance, exception_traceback):
        if not (0 < self.__entered): raise RuntimeError("not entered")
        self.__entered -= 1
        if 0 < self.__entered: return
        _api = self.__api
        if _api is None: return
        self.__api = None
        try: _api.reload()
        except docker.errors.NotFound: _api = None
        finally:
            if not (_api is None):
                try:
                    if self.__options["auto_remove"] and ("created" == _api.status): _api.remove()
                    else: _api.stop()
                except docker.errors.NotFound: pass

    def __manipulate(self, action):
        if self.__api is None: raise docker.errors.NotFound("connection lost")
        try:
            self.__api.reload()
            return action(self.__api)
        except docker.errors.NotFound:
            self.__api = None
            raise


def make(*args, **kwargs): return Object(*args, **kwargs)
