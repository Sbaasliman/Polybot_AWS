FROM python:3.9-slim
WORKDIR /app
COPY requirements1.txt .
RUN pip install -r requirements1.txt
COPY .. .
EXPOSE 8443
CMD ["python3", "app.py"]