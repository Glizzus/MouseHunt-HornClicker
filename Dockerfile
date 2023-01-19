FROM python:3.11-slim

WORKDIR /usr/src/app

COPY requirements.txt main.py ./
RUN apt-get update && apt-get install -y wget firefox-esr tesseract-ocr && \
    wget https://github.com/mozilla/geckodriver/releases/download/v0.32.0/geckodriver-v0.32.0-linux64.tar.gz -O- | tar -xz && \
    mv geckodriver /usr/local/bin && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove wget
CMD ["python3", "./main.py"]