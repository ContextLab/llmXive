#!/bin/bash
set -e

# This script verifies dependency resolution for the llmXive project.
# It installs the requirements defined in requirements.txt (created in T002a).
# It is designed to be run in a clean environment or after a fresh pip cache clear.

echo "=== llmXive Dependency Resolution Verification ==="
echo "Installing dependencies from requirements.txt..."

# Ensure pip is up to date to handle complex dependency resolution
python -m pip install --upgrade pip --quiet

# Install requirements
# Using --quiet to reduce noise, but --no-deps is NOT used; we want full resolution.
# If a conflict exists, pip will raise an error here, satisfying the "verify" requirement.
python -m pip install -r requirements.txt

echo "=== Dependency Resolution Successful ==="
echo "The following packages were installed/verified:"
python -m pip list --format=freeze | grep -E "torch|numpy|scikit-learn|sentence-transformers|transformers|pandas|scipy|llama-cpp-python|pytest|faiss-cpu"
echo "All dependencies resolved correctly."
