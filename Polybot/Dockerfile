FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8443
#CMD ["sh", "-c", "sleep 50000 && python3 app.py"]
CMD ["python3 app.py"]