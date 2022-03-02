#!/usr/bin/env docker build --pull . -t phntom/email-manager:0.1.1

FROM python:3.10
WORKDIR /app
EXPOSE 5000
ENV PYTHONPATH=/app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN sed -i'' "s/branch = getattr(element, element.replace('-','_'))/branch = getattr(branch, element.replace('-','_'))/g" /usr/local/lib/python3.10/site-packages/CloudFlare/cloudflare.py
COPY wsgi.py .
CMD ["flask", "run", "--host=0.0.0.0"]
