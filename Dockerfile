FROM python:3.8-slim-buster

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV LISTEN_PORT=5000
EXPOSE 5000

CMD ["python3", "strava.py"]
