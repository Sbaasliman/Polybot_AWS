FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8443
CMD ["ls"]
CMD ["sleep 500000000"]
CMD ["python3", "app.py"]