# syntax=docker/dockerfile:1

FROM python:alpine3.13

WORKDIR /app

#ENV FLASK_APP=api/main.py
#ENV FLASK_RUN_HOST=0.0.0.0
ENV PYTHONPATH=/app

# for pip installing from git repos
RUN apk --update add git

# for numpy
RUN apk add musl-dev linux-headers g++

# for fingerprinting
RUN apk add py3-pyaudio portaudio-dev gcc musl-dev
RUN apk add ffmpeg
RUN apk add mariadb-dev

RUN /usr/local/bin/python -m pip install --upgrade pip

COPY requirements.txt requirements.txt
RUN pip install mysqlclient
RUN pip install -r requirements.txt



COPY src src
COPY fingerprint_audio_files/AD_SameLenghtJingles AD_SameLenghtJingles
COPY src/db/inserts database

EXPOSE 5000

#CMD ["flask", "run"]
CMD ["python3", "src/main.py"]