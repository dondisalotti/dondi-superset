#!/bin/bash
set -e
set -o pipefail

# Default values
REPO="ghcr.io/dondisalotti/dondi-superset"
# Docker build and push
echo "Building and pushing Docker image: main"

docker build --target lean -t "$REPO:main" .

docker push "$REPO:main"

echo "All Docker images built and pushed successfully."
