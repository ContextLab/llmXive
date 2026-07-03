"""
Tests for T014: Synthetic Data Generator - Hold-Out Mode (GP Surrogate).
"""
import os
import sys
import csv
import tempfile
from pathlib import Path
import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from generators.synthetic_data_generator import (
    generate_holdout_synthetic_data,
    save_to_csv,
    get_git_hash
)

def test_holdout_generation_produces_data():
    """Test that holdout generation produces a list of dictionaries."""
    data = generate_holdout_synthetic_data(n_samples=10, seed=42)
    assert isinstance(data, list)
    assert len(data) == 10
    assert all(isinstance(entry, dict) for entry in data)

def test_holdout_data_has_required_fields():
    """Test that all required fields are present in holdout data."""
    required_fields = [
        "material", "defect_type", "defect_density", 
        "conductivity", "elastic_tensor_diag", "fracture_energy",
        "data_source", "version"
    ]
    data = generate_holdout_synthetic_data(n_samples=5, seed=42)
    
    for entry in data:
        for field in required_fields:
            assert field in entry, f"Missing field: {field}"
        
        # Verify data_source is correct for this mode
        assert entry["data_source"] == "gp_surrogate_holdout"

def test_holdout_data_physical_bounds():
    """Test that generated values respect physical bounds (positive values)."""
    data = generate_holdout_synthetic_data(n_samples=20, seed=42)
    
    for entry in data:
        assert entry["defect_density"] > 0
        assert entry["conductivity"] > 0
        assert entry["elastic_tensor_diag"][0] > 0
        assert entry["fracture_energy"] > 0
        
        # Check elastic tensor is a list of 6 floats
        assert isinstance(entry["elastic_tensor_diag"], list)
        assert len(entry["elastic_tensor_diag"]) == 6
        assert all(isinstance(v, (int, float)) for v in entry["elastic_tensor_diag"])

def test_holdout_generation_determinism():
    """Test that the same seed produces the same results."""
    data1 = generate_holdout_synthetic_data(n_samples=10, seed=123)
    data2 = generate_holdout_synthetic_data(n_samples=10, seed=123)
    
    assert len(data1) == len(data2)
    for e1, e2 in zip(data1, data2):
        assert e1["defect_density"] == e2["defect_density"]
        assert e1["conductivity"] == e2["conductivity"]
        assert e1["elastic_tensor_diag"] == e2["elastic_tensor_diag"]

def test_save_to_csv_creates_file():
    """Test that save_to_csv writes a valid CSV file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_holdout.csv"
        data = generate_holdout_synthetic_data(n_samples=5, seed=42)
        
        save_to_csv(data, filepath)
        
        assert filepath.exists()
        
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 5
            assert "defect_density" in rows[0]

def test_git_hash_exists():
    """Test that get_git_hash returns a string."""
    hash_val = get_git_hash()
    assert isinstance(hash_val, str)
    assert len(hash_val) > 0
