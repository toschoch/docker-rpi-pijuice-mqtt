FROM balenalib/raspberrypi3-python:3.7-build AS builder

COPY requirements.txt ./
RUN mkdir wheels && pip wheel -r requirements.txt --extra-index-url https://www.piwheels.org/simple -w wheels

FROM balenalib/raspberrypi3-python:3.7-run
RUN install_packages pijuice-base jq curl

COPY --from=builder requirements.txt .
COPY --from=builder wheels/ ./wheels/

RUN /usr/local/bin/python3.7 -m pip install --upgrade pip && \
    pip install -r requirements.txt --find-links wheels --no-index && \
    rm -r wheels

# Enable udevd so that plugged dynamic hardware devices show up in our container.
ENV UDEV=1

WORKDIR app

COPY wrapper ./wrapper
COPY main.py ./

CMD python main.py