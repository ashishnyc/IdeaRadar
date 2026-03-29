#!/bin/bash
# Run once to set up the database for the first time.
# Requires DATABASE_URL to be set in .env

set -e

source .env

echo "Enabling pgvector extension..."
psql "$DATABASE_URL" -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "Running Alembic migrations..."
venv/bin/alembic upgrade head

echo "Database setup complete."
