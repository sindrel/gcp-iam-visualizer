#!/bin/sh

# Build it
docker build -t gcp-iam-graph .

# Run it
docker run -it --rm \
--name gcp-iam-graph \
-e IAM_GRAPH_SCOPE="${IAM_GRAPH_SCOPE}" \
-e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/credentials.json \
-v $GOOGLE_APPLICATION_CREDENTIALS:/tmp/keys/credentials.json:ro \
-p 8080:8080 \
gcp-iam-graph
