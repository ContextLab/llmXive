#!/bin/bash
set -e

echo "Verifying src/requirements.txt installation..."
pip install -r src/requirements.txt

echo "Verifying code/requirements.txt installation..."
pip install -r code/requirements.txt

echo "Verifying byte-identity between requirements files..."
if cmp -s src/requirements.txt code/requirements.txt; then
  echo "Files are byte-identical."
else
  echo "Files are NOT byte-identical."
  exit 1
fi

echo "T013 verification successful."