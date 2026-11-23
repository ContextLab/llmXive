"""
Script to generate and save the feature definition schema.

This script executes the feature definition module to create the required
artifact: data/final/feature_definition_schema.json

Usage:
    python scripts/generate_feature_definition_schema.py
"""

import sys
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from src.models.feature_definition import main

if __name__ == "__main__":
    print("Generating feature definition schema...")
    schema = main()
    print("Feature definition schema generation complete.")