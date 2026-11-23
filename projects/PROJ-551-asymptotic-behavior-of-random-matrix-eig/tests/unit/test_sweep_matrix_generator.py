"""
Unit tests for T040a: sweep_matrix_generator.py
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest

# Adjust import path for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.sweep_matrix_generator import (
    generate_sweep_configs,
    save_raw_sweep_matrix,
    compute_file_sha256,
    run_sweep_generation
)

def test_generate_sweep_configs():
    """Test that the grid is generated correctly."""
    configs = generate_sweep_configs()
    assert len(configs) == 3 * 7 * 3  # 3 Ns * 7 thetas * 3 seeds
    assert all("N" in c and "theta" in c and "seed" in c for c in configs)
    assert all(c["N"] in [500, 1000, 2000] for c in configs)
    assert all(c["theta"] in [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0] for c in configs)
    assert all(c["seed"] in [42, 123, 456] for c in configs)

def test_save_raw_sweep_matrix(tmp_path):
    """Test that a single matrix is saved correctly."""
    config = {"N": 100, "theta": 2.0, "seed": 42}
    file_path = save_raw_sweep_matrix(config, tmp_path)

    assert file_path.exists()
    assert file_path.suffix == ".npy"

    # Verify content
    loaded = np.load(file_path)
    assert loaded.shape == (100, 100)
    assert loaded.dtype == np.float64

def test_compute_file_sha256(tmp_path):
    """Test checksum computation."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    checksum = compute_file_sha256(test_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)

def test_run_sweep_generation_small(tmp_path):
    """Test full sweep generation with a small subset."""
    # Create a minimal config list
    configs = [
        {"N": 50, "theta": 1.0, "seed": 42},
        {"N": 50, "theta": 2.0, "seed": 123}
    ]

    checksum_file = tmp_path / "checksums.json"
    output_dir = tmp_path / "matrices"

    result = run_sweep_generation(
        configs=configs,
        output_dir=output_dir,
        checksum_file=checksum_file
    )

    assert result["total_generated"] == 2
    assert checksum_file.exists()

    # Verify manifest content
    with open(checksum_file, "r") as f:
        manifest = json.load(f)
    
    assert manifest["total_configs"] == 2
    assert len(manifest["checksums"]) == 2
    
    # Verify files exist and checksums match
    for entry in manifest["checksums"]:
        file_path = Path(entry["file_path"])
        if not file_path.is_absolute():
            file_path = output_dir / Path(entry["file_path"]).name
        
        assert file_path.exists()
        computed_checksum = compute_file_sha256(file_path)
        assert computed_checksum == entry["checksum"]