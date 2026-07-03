#!/bin/bash
set -e
echo "Running black formatter..."
black code/
echo "Formatting complete."
