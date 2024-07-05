#!/bin/sh

# Source environment variables from .env.docker
set -o allexport; . /app/.env.docker; set +o allexport

# Print environment variables for debugging
echo "DB_USERNAME: $DB_USERNAME"
echo "DB_PASSWORD: $DB_PASSWORD"
echo "DB_HOST: $DB_HOST"
echo "DB_NAME: $DB_NAME"
# Wait for PostgreSQL to be ready
/wait-for-it.sh db:5432 -- echo "PostgreSQL is up and running"

# Start FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start Streamlit
# streamlit run app/app.py --server.port 8501 --server.address 0.0.0.0

# Wait for both processes to finish
wait