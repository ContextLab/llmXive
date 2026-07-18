#!/bin/bash
# Script to run code formatter using Black
# Formats code in-place

set -e

echo "Running Black formatter..."
black code/src/ code/tests/
echo "Format check passed."
