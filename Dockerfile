FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir code
WORKDIR /code
ADD . /code
COPY ./requirements.txt /code/requirements.txt
RUN pip3 install -r requirements.txt
COPY . /code
