import json
import os
import pytest
from pathlib import Path
import tempfile
import numpy as np

from code.residual_logger import (
    log_eigenvalue_residual,
    save_residuals_to_file,
    append_residuals_to_file,
    main
)
from code.config import get_config

@pytest.fixture
def temp_metadata_dir():
    """Create a temporary directory for metadata files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override config path temporarily
        config = get_config()
        original_dir = config.DATA_METADATA_DIR
        config.DATA_METADATA_DIR = Path(tmpdir)
        yield Path(tmpdir)
        config.DATA_METADATA_DIR = original_dir

def test_log_eigenvalue_residual_structure(temp_metadata_dir):
    """Test that log_eigenvalue_residual returns a valid dictionary structure."""
    entry = log_eigenvalue_residual(
        residual_norm=1e-10,
        convergence_flag=True,
        system_size=100,
        disorder_strength=1.0,
        realization_index=0,
        eigenvalue_index=5,
        energy=-0.5,
        method="eigh"
    )
    
    assert isinstance(entry, dict)
    assert entry["system_size"] == 100
    assert entry["disorder_strength"] == 1.0
    assert entry["realization_index"] == 0
    assert entry["eigenvalue_index"] == 5
    assert entry["energy"] == -0.5
    assert entry["residual_norm"] == 1e-10
    assert entry["converged"] is True
    assert "timestamp" in entry
    assert "solver_method" in entry

def test_save_residuals_to_file(temp_metadata_dir):
    """Test saving a batch of residuals to JSON."""
    residuals = [
        log_eigenvalue_residual(1e-10, True, 100, 1.0, 0, i, float(i), "eigh")
        for i in range(5)
    ]
    
    output_path = save_residuals_to_file(residuals)
    
    assert os.path.exists(output_path)
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 5
    assert data[0]["system_size"] == 100

def test_append_residuals_to_file(temp_metadata_dir):
    """Test appending a single entry to an existing file."""
    # First save a batch
    residuals = [
        log_eigenvalue_residual(1e-10, True, 100, 1.0, 0, i, float(i), "eigh")
        for i in range(3)
    ]
    save_residuals_to_file(residuals)
    
    # Append one more
    new_entry = log_eigenvalue_residual(1e-11, True, 100, 1.0, 0, 10, 10.0, "eigh")
    output_path = append_residuals_to_file(new_entry)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 4
    assert data[-1]["eigenvalue_index"] == 10

def test_save_overwrites_corrupted_file(temp_metadata_dir):
    """Test that save_residuals_to_file handles corrupted JSON gracefully."""
    # Create a corrupted file
    output_path = temp_metadata_dir / "residuals.json"
    with open(output_path, 'w') as f:
        f.write("not valid json {{{")
    
    # Save should succeed and overwrite
    residuals = [log_eigenvalue_residual(1e-10, True, 100, 1.0, 0, 0, 0.0, "eigh")]
    save_residuals_to_file(residuals, str(output_path))
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 1

def test_main_function_creates_file(temp_metadata_dir):
    """Test that the main function writes the expected file."""
    # Run main
    main()
    
    output_path = temp_metadata_dir / "residuals.json"
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert len(data) == 10  # As defined in main()