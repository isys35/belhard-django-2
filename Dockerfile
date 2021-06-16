FROM ubuntu:20.04

RUN apt-get update
RUN apt-get -y upgrade

RUN apt-get -y install python3-pip
RUN mkdir /srcdoc
WORKDIR /src
COPY ./requirements.txt /scripts/
RUN pip3 install -r /scripts/requirements.txt