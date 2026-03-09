#!/bin/bash
# Deploy script for Tipos Beach House
# Run this on the VPS after cloning the repo

set -e

echo "=== Tipos Beach House - Deploy ==="

# 1. Check .env exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Create it first:"
    echo "  cp .env.example .env"
    echo "  nano .env  # set DB_PASSWORD and SECRET_KEY"
    exit 1
fi

echo "1. Building and starting containers..."
docker compose up -d --build

echo "2. Waiting for database to be ready..."
sleep 5

echo "3. Running database migrations..."
docker compose exec app flask db upgrade

echo "4. Running seed (initial data)..."
docker compose exec app python seed.py

echo ""
echo "=== Deploy complete ==="
echo "The app is running on port 80 (HTTP)."
echo ""
echo "=== Next: SSL Certificate ==="
echo "Run this to get a Let's Encrypt certificate:"
echo ""
echo "  docker compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d tiposchelem.com -d www.tiposchelem.com --email TU_EMAIL --agree-tos --no-eff-email"
echo ""
echo "Then uncomment the HTTPS block in nginx/nginx.conf and run:"
echo "  docker compose restart nginx"
