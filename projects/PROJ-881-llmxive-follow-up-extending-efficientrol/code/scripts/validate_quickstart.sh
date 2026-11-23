#!/bin/bash
set -e

echo "Validating quickstart execution..."

# Check directories
DIRS=(
    "code/src/"
    "code/tests/"
    "code/data/"
    "code/docs/"
    "code/scripts/"
    "code/results/"
    "specs/001-entropy-validity-prediction/contracts/"
)

for dir in "${DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "ERROR: Directory $dir does not exist"
        exit 1
    fi
done

# Check requirements.txt
if [ ! -f "code/requirements.txt" ]; then
    echo "ERROR: requirements.txt not found"
    exit 1
fi

# Check schema
if [ ! -f "code/contracts/dataset.schema.yaml" ]; then
    echo "ERROR: dataset.schema.yaml not found"
    exit 1
fi

echo "All quickstart checks passed."
