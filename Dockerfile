FROM node:16-alpine

WORKDIR /usr/src/app
COPY package*.json index.ts tsconfig.json ./
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.32.0/geckodriver-v0.32.0-linux64.tar.gz -O- | tar -xz && \
    mv geckodriver /usr/local/bin && \
    apk update && apk add tar gzip firefox && \
    npm install
CMD ["npx", "ts-node", "index.ts"]