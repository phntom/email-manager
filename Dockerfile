#!/usr/bin/env -vS docker build --pull -t phntom/email-manager:0.1.8 . -f

FROM python:3.10
WORKDIR /app
EXPOSE 8579
ENV PYTHONPATH=/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY em em
CMD ["python3", "em/__main__.py"]
