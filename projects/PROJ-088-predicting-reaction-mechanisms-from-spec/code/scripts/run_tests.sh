#!/bin/bash
set -e

echo "Running Pytest..."
pytest tests/ -v --tb=short

echo "Tests complete."
