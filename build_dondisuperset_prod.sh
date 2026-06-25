#!/bin/bash
set -e
set -o pipefail

# Default values
REPO="ghcr.io/dondisalotti/dondi-superset"
DEFAULT_CODENAME="frankenstein"
DEFAULT_SEMVERSION="1.0.0"

# Ask user if they want to use defaults
echo "Default CODENAME: $DEFAULT_CODENAME"
echo "Default SEMVERSION: $DEFAULT_SEMVERSION"
read -p "Uso questi default? (yes/no): " USE_DEFAULTS

# Convert response to lowercase
USE_DEFAULTS=$(echo "$USE_DEFAULTS" | tr '[:upper:]' '[:lower:]')

if [[ "$USE_DEFAULTS" == "yes" || "$USE_DEFAULTS" == "y" ]]; then
    CODENAME="$DEFAULT_CODENAME"
    SEMVERSION="$DEFAULT_SEMVERSION"
else
    read -p "Enter CODENAME: " CODENAME
    read -p "Enter SEMVERSION: " SEMVERSION
fi

echo "Using CODENAME: $CODENAME"
echo "Using SEMVERSION: $SEMVERSION"

# Docker build and push
echo "Building and pushing Docker image: latest"

echo "Building and pushing Docker image: $SEMVERSION"

echo "Building and pushing Docker image: $CODENAME"

docker build --target lean -t "$REPO:latest" -t "$REPO:$SEMVERSION" -t "$REPO:$CODENAME" .

docker push "$REPO:latest"
docker push "$REPO:$SEMVERSION"
docker push "$REPO:$CODENAME"


echo "All Docker images built and pushed successfully."
