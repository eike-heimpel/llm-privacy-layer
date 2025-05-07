#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "No .env file found. Please create one based on .env.example"
    exit 1
fi

# Configuration
# Use environment variables with defaults as fallback
REMOTE_HOST="${REMOTE_HOST:-localhost}"
REMOTE_USER="${REMOTE_USER:-user}"
REMOTE_DIR="${REMOTE_DIR:-/tmp/llm-privacy-layer}"
SOURCE_DIR="$(pwd)"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Starting deployment to homeserver..."
echo "Source: $SOURCE_DIR"
echo "Destination: $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"

# Make sure remote directory exists
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to create remote directory. Exiting.${NC}"
    exit 1
fi

# Use rsync to copy files
# -a: archive mode (preserves permissions, etc.)
# -v: verbose
# -z: compress during transfer
# --delete: delete files on destination that don't exist on source
# --exclude: don't copy these directories/files
rsync -avz --delete \
    --exclude '.git/' \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.DS_Store' \
    --exclude '.env' \
    --exclude '.env.local' \
    "$SOURCE_DIR/" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "${GREEN}Files synchronized to $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR${NC}"
else
    echo -e "${RED}Deployment failed.${NC}"
    exit 1
fi

# Display remote directory contents
echo "Remote directory contents:"
ssh $REMOTE_USER@$REMOTE_HOST "ls -la $REMOTE_DIR"

exit 0 