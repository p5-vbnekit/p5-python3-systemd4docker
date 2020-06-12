ARG base_image=debian:stable

FROM ${base_image}

ENV LC_ALL C
ENV container docker
ENV DEBIAN_FRONTEND noninteractive

RUN apt update --assume-yes && apt full-upgrade --assume-yes
RUN apt update --assume-yes && apt install --assume-yes systemd
RUN apt clean --assume-yes && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN systemctl disable \
    local-fs.target systemd-remount-fs.service \
    getty.target console-getty.service \
    systemd-logind.service

RUN rm -f \
    /lib/systemd/system/multi-user.target.wants/getty.target \
    /lib/systemd/system/multi-user.target.wants/systemd-logind.service

VOLUME ["/sys/fs/cgroup", "/dev/hugepages", "/run", "/run/lock"]

ENTRYPOINT ["/lib/systemd/systemd"]
