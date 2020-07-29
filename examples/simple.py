#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import docker
import docker.errors

from p5.systemd4docker.builder import build as _build_image
from p5.systemd4docker.launcher import run as _run_container


def _main():
    def _print_message(message):
        print(message, file = sys.stderr)
        sys.stderr.flush()

    docker.from_env().images.pull("debian:stable")
    _print_message("docker pull for \"debian:stable\" was finished")

    def _build_log_delegate(message):
        sys.stderr.write(message)
        sys.stderr.flush()

    _image = _build_image(log_delegate = _build_log_delegate)
    _print_message("image was built: \"{}\"".format(_image))

    _run_container(image = _image, hostname = "systemd4docker-example")


if "__main__" == __name__: _main()
