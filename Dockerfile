FROM python:3.11-slim-bookworm

WORKDIR /python-docker

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV LISTEN_PORT=4000
EXPOSE 4000

# Copy and set executable permissions for entrypoint
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
