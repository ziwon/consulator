# Build
FROM python:3.6.9-alpine AS compile-image

RUN apk --no-cache add --virtual .build-deps \
    build-base linux-headers libffi-dev libressl-dev curl

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

# Prod
FROM python:3.6.9-alpine AS build-image
COPY --from=compile-image /opt/venv /opt/venv

ENV PYTHONUNBUFFERED=1
ENV HOST "0.0.0.0"
ENV PORT "8000"
ENV BIND_INTERFACE "eth0"

RUN apk add --no-cache curl
RUN mkdir /app
WORKDIR /app
ADD . .
ENV PATH="/opt/venv/bin:$PATH"
ENTRYPOINT ["./docker-entry.sh"]