FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    your-package-here \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN ./build.sh

CMD ["python app.py"]