#!/bin/bash

set -e

LAYER_NAME="layer"
PYTHON_VERSION="3.11"

# Step 1: Setup directory structure
rm -rf $LAYER_NAME
mkdir -p $LAYER_NAME/python
cd $LAYER_NAME

# Step 2: Create requirements.txt
cat <<EOF > requirements.txt
boto3
requests
supabase
logging
EOF

# Step 3: Create Dockerfile
cat <<EOF > Dockerfile
FROM public.ecr.aws/lambda/python:${PYTHON_VERSION}

RUN pip install --upgrade pip

COPY requirements.txt ./
RUN pip install -r requirements.txt -t python/
EOF

# Step 4: Build Docker image
docker build --platform linux/amd64 -t ${LAYER_NAME}_builder .

# Step 5: Extract dependencies from container
CONTAINER_ID=$(docker create ${LAYER_NAME}_builder)
docker cp $CONTAINER_ID:/var/task/python ./python
docker rm $CONTAINER_ID

# Step 6: Zip the layer
cd python
zip -r9 ../layer.zip .
cd ..

echo "✅ Lambda layer built: $LAYER_NAME/layer.zip"

