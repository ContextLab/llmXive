#!/bin/bash
set -e

echo "Checking code format (black)..."
black --check code/ src/ tests/

echo "Format check passed."
