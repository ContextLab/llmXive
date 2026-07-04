import json
import numpy as np
import hashlib
import pytest
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from generate_data import generate_correlated_data, generate_sweep_data, verify_metadata_file
from utils.simulation import SimulationConfig

def test_metadata_file_structure(tmp_path):
    """Test that generate_sweep_data writes correct metadata structure."""
    config = SimulationConfig(
        n_values=[100],
        p_values=[50],
        rho_values=[0.1],
        distribution_types=["normal"],
        seeds=[12345],
        n_iterations=1
    )
    
    output_dir = str(tmp_path)
    generated_files = generate_sweep_data(config, output_dir)
    
    assert len(generated_files) == 1
    filepath = generated_files[0]
    
    # Verify file exists
    assert Path(filepath).exists()
    
    # Verify JSON structure
    with open(filepath, 'r') as f:
        metadata = json.load(f)
    
    required_keys = ["sha256", "rho", "n", "p", "distribution_type", "seed"]
    for key in required_keys:
        assert key in metadata, f"Missing key: {key}"
    
    assert metadata["seed"] == 12345
    assert metadata["n"] == 100
    assert metadata["p"] == 50
    assert metadata["rho"] == 0.1
    assert metadata["distribution_type"] == "normal"
    assert isinstance(metadata["sha256"], str)
    assert len(metadata["sha256"]) == 64  # SHA256 hex length

def test_sha256_consistency(tmp_path):
    """Test that the stored sha256 matches the actual data hash."""
    # Generate data manually to verify hash
    n, p, rho, seed = 100, 50, 0.1, 99999
    data, _ = generate_correlated_data(n=n, p=p, rho=rho, seed=seed)
    
    expected_hash = hashlib.sha256(data.tobytes()).hexdigest()
    
    # Create a fake data file to test verification
    data_path = tmp_path / f"{seed}_data.npy"
    np.save(data_path, data)
    
    # Create metadata file
    meta_content = {
        "sha256": expected_hash,
        "rho": rho,
        "n": n,
        "p": p,
        "distribution_type": "normal",
        "seed": seed
    }
    meta_path = tmp_path / f"{seed}.json"
    with open(meta_path, 'w') as f:
        json.dump(meta_content, f)
    
    # Verify
    assert verify_metadata_file(str(meta_path)) is True
    
    # Test with wrong hash
    meta_content["sha256"] = "wrong_hash_value"
    with open(meta_path, 'w') as f:
        json.dump(meta_content, f)
    
    assert verify_metadata_file(str(meta_path)) is False

def test_generate_sweep_multiple_seeds(tmp_path):
    """Test generation with multiple seeds."""
    config = SimulationConfig(
        n_values=[50],
        p_values=[20],
        rho_values=[0.0, 0.5],
        distribution_types=["normal", "t"],
        seeds=[1, 2, 3],
        n_iterations=1
    )
    
    output_dir = str(tmp_path)
    generated_files = generate_sweep_data(config, output_dir)
    
    # Total combinations: 1(n) * 1(p) * 2(rho) * 2(dist) * 3(seeds) = 12
    # But generate_sweep_data iterates over seeds for each combination
    # Actually, looking at the implementation, it iterates over all combinations
    # n_values * p_values * rho_values * distribution_types * seeds
    # 1 * 1 * 2 * 2 * 3 = 12
    assert len(generated_files) == 12
    
    # Verify all files exist and have unique seeds
    for f in generated_files:
        assert Path(f).exists()
        with open(f, 'r') as fp:
            meta = json.load(fp)
            assert "seed" in meta
    
    # Check that we have the expected seeds
    seeds_found = set()
    for f in generated_files:
        with open(f, 'r') as fp:
            meta = json.load(fp)
            seeds_found.add(meta["seed"])
    
    assert seeds_found == {1, 2, 3}