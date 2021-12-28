FROM ubuntu:latest

WORKDIR /usr/local/src

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update
RUN apt install -y python3 python3-pip openscad

ARG USERNAME="scan2stl"
RUN useradd -m $USERNAME
COPY ./requirements.txt ./
RUN pip3 install -r requirements.txt
