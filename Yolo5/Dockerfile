FROM ultralytics/yolov5:latest-cpu

# Set the working directory
WORKDIR /usr/src/app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Download YOLOv5 model weights
RUN curl -L https://github.com/ultralytics/yolov5/releases/download/v6.1/yolov5s.pt -o yolov5s.pt

# Copy your application code
COPY . .

# Add trusted root certificates
COPY ca-certificates.crt /etc/ssl/certs/

EXPOSE 80
#CMD ["sh", "-c", "sleep 5000000 && python3 app.py"]
# Command to run your application
CMD ["python3", "app.py"]
