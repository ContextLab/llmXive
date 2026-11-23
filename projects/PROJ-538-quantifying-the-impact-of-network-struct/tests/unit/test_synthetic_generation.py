"""
Unit tests for SyntheticDataGenerator (T014).
Verifies that the generated data has the correct structure and meets the
ground truth correlation requirement (r=0.6).
"""
import pytest
import numpy as np
import json
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from synthetic import SyntheticDataGenerator, run_synthetic_generation
from utils import DataIntegrityError

def test_synthetic_structure():
    """Test that the generated snapshots have the correct structure."""
    generator = SyntheticDataGenerator(n_snapshots=5, seed=42)
    snapshots = generator.generate_all()
    
    assert len(snapshots) == 5
    for s in snapshots:
        assert hasattr(s, "positions")
        assert hasattr(s, "species")
        assert hasattr(s, "thermal_conductivity")
        assert hasattr(s, "defect_density")
        assert len(s.positions) == len(s.species)
        assert s.thermal_conductivity > 0

def test_correlation_ground_truth():
    """
    Verify that the generated dataset has a recoverable correlation 
    between defect density and thermal conductivity within ±0.05 of 0.6.
    """
    generator = SyntheticDataGenerator(n_snapshots=50, seed=42)
    snapshots = generator.generate_all()
    
    defect_densities = [s.defect_density for s in snapshots]
    conductivities = [s.thermal_conductivity for s in snapshots]
    
    r, _ = np.corrcoef(defect_densities, conductivities)[0, 1]
    
    # The task requires r=0.6 within ±0.05
    assert abs(r - 0.6) <= 0.05, f"Correlation r={r:.4f} is not within tolerance of 0.6"

def test_run_synthetic_generation_writes_file(tmp_path):
    """Test that run_synthetic_generation writes a valid JSON file."""
    output_file = tmp_path / "test_snapshots.json"
    
    run_synthetic_generation(
        output_path=str(output_file),
        n_snapshots=10,
        seed=42
    )
    
    assert output_file.exists()
    
    with open(output_file, "r") as f:
        data = json.load(f)
        
    assert "snapshots" in data
    assert len(data["snapshots"]) == 10
    assert "metadata" in data
    assert data["metadata"]["n_snapshots"] == 10

def test_unique_seeds():
    """Test that each snapshot has a unique seed."""
    generator = SyntheticDataGenerator(n_snapshots=10, seed=100)
    snapshots = generator.generate_all()
    
    seeds = [s.seed for s in snapshots]
    assert len(seeds) == len(set(seeds))
    assert seeds == list(range(100, 110))
