#!/bin/bash
set -e

echo "Formatting code with Black..."
black code/ tests/

echo "Code formatted successfully."
