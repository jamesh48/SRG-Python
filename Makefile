.PHONY: help build up down restart logs logs-app logs-localstack clean rebuild shell shell-localstack health setup-tables recreate-activities test stop

# Default target
help:
	@echo "SRG-Python Docker Commands"
	@echo "============================"
	@echo ""
	@echo "  make build          - Build Docker containers"
	@echo "  make up             - Start containers in background"
	@echo "  make up-logs        - Start containers with logs"
	@echo "  make down           - Stop and remove containers"
	@echo "  make stop           - Stop containers without removing"
	@echo "  make restart        - Restart all containers"
	@echo "  make rebuild        - Rebuild containers from scratch and start"
	@echo "  make logs           - View logs from all containers"
	@echo "  make logs-app       - View logs from app container only"
	@echo "  make logs-localstack - View logs from localstack container only"
	@echo "  make shell          - Open shell in app container"
	@echo "  make shell-localstack - Open shell in localstack container"
	@echo "  make health         - Check app health endpoint"
	@echo "  make setup-tables   - Manually run setup_localstack.py"
	@echo "  make recreate-activities - Recreate activities table with new GSIs"
	@echo "  make clean          - Stop containers and remove volumes"
	@echo "  make test           - Run tests"
	@echo ""

# Build containers
build:
	docker-compose build

# Start containers in background
up:
	docker-compose up -d

# Start containers with logs
up-logs:
	docker-compose up

# Stop and remove containers
down:
	docker-compose down

# Stop containers without removing
stop:
	docker-compose stop

# Restart containers
restart:
	docker-compose restart

# Rebuild everything from scratch
rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "Containers rebuilt and started!"
	@echo "View logs with: make logs"

# View all logs
logs:
	docker-compose logs -f

# View app logs only
logs-app:
	docker-compose logs -f app

# View localstack logs only
logs-localstack:
	docker-compose logs -f localstack

# Clean everything (including volumes)
clean:
	docker-compose down -v
	@echo "Containers and volumes removed"

# Open shell in app container
shell:
	docker-compose exec app /bin/bash

# Open shell in localstack container
shell-localstack:
	docker-compose exec localstack /bin/bash

# Check health endpoint
health:
	@echo "Checking health endpoint..."
	@curl -s http://localhost:4000/srg/healthcheck && echo "" || echo "Health check failed!"

# Manually setup tables (if needed)
setup-tables:
	docker-compose exec app python3 setup_localstack.py

# Recreate activities table with new GSIs
recreate-activities:
	@echo "Recreating activities table with new GSIs..."
	docker-compose exec app python3 recreate_activities_table.py
	@echo "Done! Remember to re-import your activities data with /srg/addAllActivities"

# Run tests
test:
	docker-compose exec app python3 -m pytest
