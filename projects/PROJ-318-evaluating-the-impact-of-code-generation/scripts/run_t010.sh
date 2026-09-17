#!/bin/bash
set -e
echo "Running T010: Fetch and freeze repository list..."
python code/utils/repo_fetcher.py
echo "Verifying output..."
if [ -f "data/raw/frozen_repo_list.json" ]; then
    count=$(python -c "import json; print(len(json.load(open('data/raw/frozen_repo_list.json'))))")
    if [ "$count" -eq 20 ]; then
        echo "SUCCESS: frozen_repo_list.json contains exactly 20 items."
    else
        echo "FAILURE: frozen_repo_list.json contains $count items, expected 20."
        exit 1
    fi
else
    echo "FAILURE: data/raw/frozen_repo_list.json not found."
    exit 1
fi
if [ -f "data/raw/repo_list.json" ]; then
    echo "SUCCESS: repo_list.json exists."
else
    echo "FAILURE: data/raw/repo_list.json not found."
    exit 1
fi
echo "T010 verification passed."