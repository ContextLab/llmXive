#!/bin/bash
# Script to execute T001a setup
# This script runs the Python setup module to create directories and README

set -e

echo "Running T001a: Create project directory structure..."

# Ensure we are in the correct context (assuming repo root)
python code/setup_project_structure.py

echo "T001a execution finished."
