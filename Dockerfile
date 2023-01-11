FROM python:3.10

WORKDIR ./app
COPY . .
RUN pip install --upgrade pip && pip install --no-cache-dir --upgrade -r requirements.txt

RUN apt update
RUN apt install -y wget
RUN mkdir -p ~/.postgresql && \
    wget "https://storage.yandexcloud.net/cloud-certs/CA.pem" -O ~/.postgresql/root.crt && \
    chmod 0600 ~/.postgresql/root.crt

RUN crontab /app/mycrontab

CMD gunicorn -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker main:app --reload