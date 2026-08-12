#!/bin/bash
# Script to run ruff linting on the project

set -e

echo "Running ruff linting..."
ruff check code/ tests/

echo "Linting completed successfully!"
