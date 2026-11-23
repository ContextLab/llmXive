#!/bin/bash
set -e
DIRS=("code" "code/utils" "data/raw/repos" "data/processed" "tests/unit" "tests/integration" "state" "logs")
mkdir -p "${DIRS[@]}"
echo -n "" > logs/setup.log
for dir in "${DIRS[@]}"; do
    echo "$dir" >> logs/setup.log
done