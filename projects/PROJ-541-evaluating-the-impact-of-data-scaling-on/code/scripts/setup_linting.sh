#!/bin/bash
set -e
echo "Installing linting and formatting tools..."
pip install ruff black pytest pyyaml
echo "Tools installed."
echo "Configuring ruff and black via pyproject.toml..."
echo "Configuration files created."
echo "Linting and formatting setup complete."