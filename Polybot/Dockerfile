FROM python:3.9-slim
WORKDIR /usr/src/app
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       iputils-ping \
       dnsutils \
       python3 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8443
#CMD ["sh", "-c", "sleep 500000 && python3 app.py"]
CMD ["python3 app.py"]
