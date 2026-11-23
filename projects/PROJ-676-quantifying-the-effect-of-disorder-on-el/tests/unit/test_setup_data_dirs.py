"""
Unit tests for setup_data_dirs.py
Verifies that the directory structure is created and the provenance schema is valid.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to import the main function from setup_data_dirs
# Since the script is in code/, we add it to sys.path if necessary
import sys
from pathlib import Path

# Add the code directory to the path if running from tests
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_data_dirs import main


def test_directory_structure_creation(tmp_path):
    """Test that the required directories are created."""
    # Change to the temp directory to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        main()

        # Verify directories exist
        assert (tmp_path / "data").exists()
        assert (tmp_path / "data/raw").exists()
        assert (tmp_path / "data/processed").exists()
        assert (tmp_path / "data/metadata").exists()
    finally:
        os.chdir(original_cwd)


def test_provenance_schema_file(tmp_path):
    """Test that the provenance.json schema file is created and valid."""
    original_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        main()

        provenance_path = tmp_path / "data/metadata/provenance.json"
        assert provenance_path.exists()

        # Verify it's valid JSON
        with open(provenance_path, "r", encoding="utf-8") as f:
            schema = json.load(f)

        # Verify required keys
        assert "project_id" in schema
        assert "created_at" in schema
        assert "entries" in schema
        assert schema["properties"]["project_id"]["const"] == "PROJ-676-quantifying-the-effect-of-disorder-on-el"
    finally:
        os.chdir(original_cwd)