FROM python:3.10-slim

# FFmpeg और जरूरी पैकेज इंस्टॉल करें
RUN apt-get update && \
    apt-get install -y ffmpeg gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements इंस्टॉल करें
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# बाकी सारा कोड कॉपी करें
COPY . .

# पोर्ट एक्सपोज़ करें
EXPOSE 8080

# बॉट चालू करने की कमांड
CMD ["python", "main.py"]
