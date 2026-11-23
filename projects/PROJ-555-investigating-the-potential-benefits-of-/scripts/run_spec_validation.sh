#!/bin/bash
# Script to run the T001b spec validation
# Exits with code 1 if validation fails, 0 if passed.

set -e

echo "Running T001b Spec Validation..."
python code/spec_validation.py

echo "T001b Validation Completed Successfully."