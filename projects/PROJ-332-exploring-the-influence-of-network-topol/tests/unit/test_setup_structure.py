import os
import tempfile
import shutil
import pytest
from pathlib import Path

# We need to import setup_structure from the code directory
# Adjust the import path to match the project structure
import sys
project_root = Path(__file__).parent.parent.parent
code_dir = project_root / 'code'
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_structure import main

def test_data_directories_created(tmp_path):
    """Test that the data directory structure is created correctly."""
    # Mock the base directory to use a temporary directory
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Run the main function
        result = main()

        # Verify return code
        assert result == 0

        # Check that directories exist
        data_dir = tmp_path / 'data'
        assert data_dir.exists()
        assert (data_dir / 'raw').exists()
        assert (data_dir / 'processed').exists()
        assert (data_dir / 'interim').exists()

        # Check that .gitkeep files exist
        assert (data_dir / 'raw' / '.gitkeep').exists()
        assert (data_dir / 'processed' / '.gitkeep').exists()
        assert (data_dir / 'interim' / '.gitkeep').exists()

        # Verify .gitkeep files are empty
        for gitkeep in [
            data_dir / 'raw' / '.gitkeep',
            data_dir / 'processed' / '.gitkeep',
            data_dir / 'interim' / '.gitkeep'
        ]:
            assert gitkeep.stat().st_size == 0

    finally:
        os.chdir(original_dir)

def test_no_data_files_created(tmp_path):
    """Test that no data files are created during setup."""
    original_dir = os.getcwd()
    os.chdir(tmp_path)

    try:
        main()

        # Verify no CSV or JSON files were created
        data_dir = tmp_path / 'data'
        assert not (data_dir / 'raw' / 'simulation_results.csv').exists()
        assert not (data_dir / 'processed' / 'simulation_results.csv').exists()
        assert not (data_dir / 'interim' / 'batch_*.json').exists()

    finally:
        os.chdir(original_dir)