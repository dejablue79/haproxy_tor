FROM python:3-slim

ENV haproxy_port=5000
ENV number_of_socks=10
ENV starting_socks_port=6080
ENV starting_control_port=7080

WORKDIR /usr/src/app

RUN apt-get update \
 && apt-get install -y --no-install-recommends haproxy tor \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

COPY . .

CMD [ "python", "./main.py" ]