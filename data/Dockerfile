ARG base_image=debian:stable

FROM ${base_image}

ENV LC_ALL C
ENV container docker
ENV DEBIAN_FRONTEND noninteractive

RUN apt update --assume-yes && apt full-upgrade --assume-yes
RUN apt update --assume-yes && apt install --assume-yes apt-utils
RUN apt update --assume-yes && apt install --assume-yes systemd python3

COPY usr/local/lib/systemd/system/p5-systemd4docker-keep_alive.service /usr/local/lib/systemd/system/p5-systemd4docker-keep_alive.service
COPY usr/local/lib/systemd/system/p5-systemd4docker-keep_alive.socket /usr/local/lib/systemd/system/p5-systemd4docker-keep_alive.socket
COPY usr/local/lib/p5/systemd4docker/keep_alive/main.py /usr/local/lib/p5/systemd4docker/keep_alive/main.py
COPY usr/local/lib/p5/systemd4docker/keep_alive/touch.py /usr/local/lib/p5/systemd4docker/keep_alive/touch.py

RUN chmod +x \
    /usr/local/lib/p5/systemd4docker/keep_alive/main.py \
    /usr/local/lib/p5/systemd4docker/keep_alive/touch.py

RUN apt clean --assume-yes && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN systemctl enable p5-systemd4docker-keep_alive.service p5-systemd4docker-keep_alive.socket

RUN systemctl disable \
    local-fs.target systemd-remount-fs.service \
    getty.target console-getty.service \
    systemd-logind.service

RUN rm -f \
    /lib/systemd/system/multi-user.target.wants/getty.target \
    /lib/systemd/system/multi-user.target.wants/systemd-logind.service

VOLUME ["/sys/fs/cgroup", "/dev/hugepages", "/run", "/run/lock"]

ENTRYPOINT ["/lib/systemd/systemd"]
