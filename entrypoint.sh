#!/bin/sh
TARGET_DIR=/tmp/gcp-iam-graph
PORT=8080

if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "GOOGLE_APPLICATION_CREDENTIALS not set"
  exit 1
fi

if [ -z "$IAM_GRAPH_SCOPE" ]; then
  echo "IAM_GRAPH_SCOPE not set (e.g. 'organizations/9723823713')"
  exit 1
fi

mkdir -p ${TARGET_DIR}/src/assets
cp -r src/assets ${TARGET_DIR}/src
cp -r src/assets/img/* ${TARGET_DIR}

python3 src/create_graph.py ${IAM_GRAPH_SCOPE} ${TARGET_DIR}/index.html && \
python3 -m http.server -d ${TARGET_DIR} ${PORT}
