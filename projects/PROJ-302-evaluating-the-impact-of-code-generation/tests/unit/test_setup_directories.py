import os
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "code"))

from setup_directories import create_directories

def test_create_directories():
    """
    Test that create_directories creates the required subdirectories.
    """
    # Get the base path (project root)
    base_path = Path(__file__).resolve().parents[2]
    data_path = base_path / "data"
    raw_path = data_path / "raw"
    processed_path = data_path / "processed"

    # Run the function
    result = create_directories()

    # Assert the function returned True
    assert result is True

    # Assert the directories exist
    assert raw_path.exists()
    assert raw_path.is_dir()
    assert processed_path.exists()
    assert processed_path.is_dir()

    # Assert .gitkeep files exist
    assert (raw_path / ".gitkeep").exists()
    assert (processed_path / ".gitkeep").exists()
