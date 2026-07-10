#!/bin/bash
# Script to execute the project setup for PROJ-247
# This script runs the setup_project.py module to create the directory structure.

set -e

echo "Starting project setup for PROJ-247..."

# Change to the code directory to run the script
cd "$(dirname "$0")/../code"

python setup_project.py

echo "Setup completed successfully."