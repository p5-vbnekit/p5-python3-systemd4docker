#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import docker
import docker.errors

from . dockerfile import path as _base_image_dockerfile_path
from . build_context import path as _base_image_build_context_path


class Defaults(object):
    rm = True
    pull = False
    forcerm = True
    custom_context = False


def build(docker_options = None, log_delegate = None):
    if docker_options is None:
        return build(
            docker_options = dict(tag = "p5/systemd4docker-debian", dockerfile = _base_image_dockerfile_path, path = _base_image_build_context_path),
            log_delegate = log_delegate
        )

    _errors = []
    _result = None
    _build_log = []

    _docker_options = dict(**docker_options)
    _docker_options.setdefault("rm", Defaults.rm)
    _docker_options.setdefault("pull", Defaults.pull)
    _docker_options.setdefault("forcerm", Defaults.forcerm)
    _docker_options.setdefault("custom_context", Defaults.custom_context)

    def _restore_errors():
        if not _errors: return
        try: raise docker.errors.BuildError(*(_errors.pop()))
        finally: _restore_errors()

    def _make_result(aux_message):
        if not ("ID" in aux_message): return None
        _match = re.search(r"(^sha256:)([0-9a-f]+)$", aux_message["ID"])
        if not _match: return None
        return _match.group(2)

    if log_delegate is None:
        # noinspection PyUnusedLocal
        def _log_delegate(message): pass
    else: _log_delegate = log_delegate

    _response_stream = docker.APIClient().build(**_docker_options)

    try:
        try:
            for _message in _response_stream:
                _message = json.loads(_message.decode("utf-8"))
                _build_log.append(_message)
                if "aux" in _message: _result = _make_result(_message["aux"])
                if "errorDetail" in _message: _errors.append((_message["errorDetail"]["message"], tuple(_build_log)))
                if "stream" in _message: _log_delegate(_message["stream"])

            if (not _errors) and (_result is None): raise RuntimeError("result expected")
            return _result

        finally:
            if _errors: _restore_errors()

    except docker.errors.BuildError: raise
    except BaseException as _exception: raise docker.errors.BuildError(reason = _exception, build_log = tuple(_build_log)) from _exception
