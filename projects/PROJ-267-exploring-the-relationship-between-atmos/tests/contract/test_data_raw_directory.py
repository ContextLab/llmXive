"""Contract test for data/raw directory creation (Task T003).

This test verifies that the data/raw directory exists and is a valid directory
after running the data/raw directory creation script.
"""

from pathlib import Path
import pytest


def test_data_raw_directory_exists():
    """Test that the data/raw directory exists after running the creation script.

    The data/raw directory is required for storing raw downloaded datasets
    (GRACE-FO mascon solutions and NOAA CPC Atmospheric River Catalog data)
    before preprocessing, as specified in task T003.
    """
    # Project root is three levels up from tests/contract/
    project_root = Path(__file__).resolve().parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"

    assert data_raw_dir.exists(), (
        f"data/raw directory does not exist at {data_raw_dir}. "
        "Run code/create_data_raw_directory.py to create it."
    )
    assert data_raw_dir.is_dir(), (
        f"data/raw is not a directory at {data_raw_dir}"
    )
