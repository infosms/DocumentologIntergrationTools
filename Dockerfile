FROM python:3.8.3-slim-buster

RUN apt-get update && apt-get -y install libpq-dev gcc
RUN apt-get install -y vim
RUN apt-get install -y curl
WORKDIR /usr/src/app

# install dependencies
RUN pip install requests
RUN pip install lxml
COPY ./generate_json.py .
COPY ./config.py .

CMD tail -f /dev/null
