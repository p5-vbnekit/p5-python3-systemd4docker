#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import docker
from p5.systemd4docker.launcher import run as _run_container
from p5.systemd4docker.dockerfile import path as _dockerfile_path


def _main():
    _name = "debian-stable-systemd-example"

    with open(_dockerfile_path, "rb") as _dockerfile_stream:
        docker.from_env().images.build(tag = _name, fileobj = _dockerfile_stream, rm = True, pull = True, forcerm = True, custom_context = False)

    _run_container(name = _name, image = _name, hostname = _name)


if "__main__" == __name__: _main()
