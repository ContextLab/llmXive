"""
Unit tests for Task T019: Atomic Data Hygiene.

Verifies:
1. Matrix generation produces correct shape.
2. File is saved to correct location.
3. Checksum is computed correctly.
4. Manifest is updated correctly.
"""
import json
import os
import tempfile
from pathlib import Path
import numpy as np
import pytest

# Mock the config to use temporary directories
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analysis.task019_hygiene import run_hygiene_capture, compute_file_sha256, load_existing_checksums

@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        data_raw = Path(tmpdir) / "data" / "raw"
        state = Path(tmpdir) / "state"
        data_raw.mkdir(parents=True)
        state.mkdir(parents=True)
        yield {
            "data_raw": data_raw,
            "state": state
        }

def test_matrix_generation_and_saving(temp_dirs):
    """Test that a matrix is generated and saved correctly."""
    seed = 42
    n = 100
    
    result = run_hygiene_capture(
        seed=seed,
        n=n,
        output_dir=temp_dirs["data_raw"],
        state_dir=temp_dirs["state"]
    )

    # Check result keys
    assert "filename" in result
    assert "checksum" in result
    assert result["N"] == n
    assert result["seed"] == seed

    # Check file exists
    expected_path = temp_dirs["data_raw"] / result["filename"]
    assert expected_path.exists()

    # Check content
    loaded_matrix = np.load(expected_path)
    assert loaded_matrix.shape == (n, n)
    # Verify it's symmetric (Wigner matrix property)
    assert np.allclose(loaded_matrix, loaded_matrix.T)

def test_checksum_consistency(temp_dirs):
    """Test that the computed checksum matches the file content."""
    seed = 123
    n = 50
    
    run_hygiene_capture(
        seed=seed,
        n=n,
        output_dir=temp_dirs["data_raw"],
        state_dir=temp_dirs["state"]
    )

    # Find the file
    files = list(temp_dirs["data_raw"].glob("*.npy"))
    assert len(files) == 1
    
    file_path = files[0]
    computed_hash = compute_file_sha256(file_path)

    # Load manifest
    manifest_path = temp_dirs["state"] / "checksums_raw.json"
    manifest = load_existing_checksums(manifest_path)

    assert len(manifest["entries"]) == 1
    assert manifest["entries"][0]["checksum"] == computed_hash

def test_manifest_update(temp_dirs):
    """Test that the manifest is updated atomically and correctly."""
    seed = 42
    n = 100
    
    # First run
    run_hygiene_capture(
        seed=seed,
        n=n,
        output_dir=temp_dirs["data_raw"],
        state_dir=temp_dirs["state"]
    )

    manifest_path = temp_dirs["state"] / "checksums_raw.json"
    manifest = load_existing_checksums(manifest_path)

    assert "entries" in manifest
    assert len(manifest["entries"]) == 1
    assert manifest["entries"][0]["metadata"]["seed"] == seed

    # Run again with different seed
    seed2 = 999
    run_hygiene_capture(
        seed=seed2,
        n=n,
        output_dir=temp_dirs["data_raw"],
        state_dir=temp_dirs["state"]
    )

    manifest = load_existing_checksums(manifest_path)
    assert len(manifest["entries"]) == 2
    
    seeds_in_manifest = [e["metadata"]["seed"] for e in manifest["entries"]]
    assert seed in seeds_in_manifest
    assert seed2 in seeds_in_manifest
