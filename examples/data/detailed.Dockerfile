ARG base_image
FROM ${base_image}

COPY usr/local/lib/systemd/system/p5-systemd4docker-example.service /usr/local/lib/systemd/system/p5-systemd4docker-example.service
COPY usr/local/lib/systemd/system/p5-systemd4docker-wait_for-example_service.target /usr/local/lib/systemd/system/p5-systemd4docker-wait_for-example_service.target

RUN systemctl enable p5-systemd4docker-example.service p5-systemd4docker-wait_for-example_service.target

RUN apt update --assume-yes && apt full-upgrade --assume-yes
RUN apt autoremove --purge --assume-yes && apt clean --assume-yes && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
