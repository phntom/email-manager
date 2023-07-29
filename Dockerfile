#!/usr/bin/env -vS docker build --pull -t phntom/email-manager:0.1.23 . -f

FROM python:3.10
WORKDIR /app
EXPOSE 8579
ENV PYTHONPATH=/app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache
COPY em em
CMD ["python3", "em/__main__.py"]
