#!/bin/bash
set -e

echo "Waiting for LocalStack to be ready..."

# Wait for LocalStack to be available
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localstack:4566/_localstack/health > /dev/null 2>&1; then
        echo "LocalStack is ready!"
        break
    fi
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - LocalStack not ready yet, waiting..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: LocalStack did not become ready in time"
    exit 1
fi

# Give it an extra second to fully initialize
sleep 2

echo "Setting up DynamoDB tables..."
python3 setup_localstack.py

echo "Starting Flask application..."
exec python3 strava.py
