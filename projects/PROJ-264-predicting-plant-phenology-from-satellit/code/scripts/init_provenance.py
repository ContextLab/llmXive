"""
Script to initialize the data/provenance.yaml file.
This script is the executable entry point for Task T007.
"""
import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.provenance import initialize_provenance_file, PROVENANCE_FILE_PATH


def main():
    """Initialize the provenance file."""
    print(f"Initializing provenance file at: {PROVENANCE_FILE_PATH}")
    initialize_provenance_file()
    print("Success: provenance.yaml has been created.")
    print("Schema: version, created_at, entries (list of dicts with checksums, params, etc.)")


if __name__ == "__main__":
    main()