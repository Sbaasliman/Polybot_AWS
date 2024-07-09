FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y python3
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8443
CMD ["sh", "-c", "sleep 500000 && python3 app.py"]
#CMD ["python3 app.py"]