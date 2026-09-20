#!/bin/bash
set -e
echo "Running formatter (black)..."
black code/ tests/
echo "Formatting completed."
