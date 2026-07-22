import os
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_directories import create_project_directories

def test_create_project_directories():
    """Test that the required directories are created."""
    # Run the function
    result = create_project_directories()
    
    # Assert it returned True
    assert result is True
    
    # Verify directories exist
    base_path = Path(__file__).resolve().parent.parent.parent
    project_root = base_path / "projects" / "PROJ-271-evaluating-the-effectiveness-of-llms-for"
    
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    results_dir = project_root / "results"
    
    assert data_raw.exists(), f"Directory {data_raw} was not created"
    assert data_processed.exists(), f"Directory {data_processed} was not created"
    assert results_dir.exists(), f"Directory {results_dir} was not created"
    
    # Verify they are directories
    assert data_raw.is_dir(), f"{data_raw} is not a directory"
    assert data_processed.is_dir(), f"{data_processed} is not a directory"
    assert results_dir.is_dir(), f"{results_dir} is not a directory"
