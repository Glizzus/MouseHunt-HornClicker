FROM node:16

WORKDIR /usr/src/app
COPY package*.json index.ts tsconfig.json captcha.py requirements.txt ./
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.32.0/geckodriver-v0.32.0-linux64.tar.gz -O- | tar -xz && \
    mv geckodriver /usr/local/bin && \
    apt-get update && apt-get install -y firefox-esr python3 python3-pip tesseract-ocr && \
    npm install && \
    python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt
CMD ["npx", "ts-node", "index.ts"]