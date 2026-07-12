"""
Tests for the Synthetic Data Generator.

Verifies:
- Correct implementation of analytical models
- Output file creation
- Required fields presence
- Seed reproducibility
"""
import os
import csv
import json
import tempfile
from pathlib import Path
import sys
import numpy as np

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from generators.synthetic_data_generator import (
    get_git_hash,
    generate_synthetic_defect_data,
    apply_griffith_criterion,
    apply_rule_of_mixtures,
    apply_matthiessen_rule
)

def test_git_hash():
    """Test that git hash function returns a string."""
    git_hash = get_git_hash()
    assert isinstance(git_hash, str)
    assert len(git_hash) > 0
    print(f"Git hash: {git_hash}")

def test_griffith_criterion():
    """Test Griffith criterion calculation."""
    E = 1000e9  # Pa
    gamma = 0.1  # J/m^2
    a = 10e-9  # m (10 nm crack)
    
    sigma_c = apply_griffith_criterion(E, gamma, a)
    
    # Expected: sqrt(2 * 1000e9 * 0.1 / (pi * 10e-9))
    expected = np.sqrt((2 * E * gamma) / (np.pi * a))
    
    assert np.isclose(sigma_c, expected)
    assert sigma_c > 0
    print(f"Griffith test passed: sigma_c = {sigma_c:.2e} Pa")

def test_rule_of_mixtures():
    """Test Rule of Mixtures calculation."""
    P_pristine = 100
    P_defect = 10
    f = 0.2  # 20% defect fraction
    
    P_eff = apply_rule_of_mixtures(P_pristine, P_defect, f)
    expected = (1 - f) * P_pristine + f * P_defect
    
    assert np.isclose(P_eff, expected)
    assert P_defect <= P_eff <= P_pristine
    print(f"Rule of Mixtures test passed: P_eff = {P_eff}")

def test_matthiessen_rule():
    """Test Matthiessen's rule calculation."""
    sigma_0 = 1e7  # S/m
    scattering = 10.0  # Coefficient
    
    sigma_eff = apply_matthiessen_rule(sigma_0, scattering)
    expected = sigma_0 / (1 + scattering)
    
    assert np.isclose(sigma_eff, expected)
    assert sigma_eff < sigma_0
    print(f"Matthiessen test passed: sigma_eff = {sigma_eff:.2e} S/m")

def test_synthetic_data_generation():
    """Test full synthetic data generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_synthetic.csv"
        
        records = generate_synthetic_defect_data(
            n_samples=10,
            seed=42,
            output_path=str(output_path)
        )
        
        # Check record count
        assert len(records) == 10
        
        # Check required fields
        required_fields = [
            'id', 'material', 'defect_type', 'defect_density',
            'conductivity_S_m', 'elastic_modulus_Pa', 'fracture_energy_J_m2',
            'elastic_tensor', 'data_source', 'git_hash'
        ]
        
        for record in records:
            for field in required_fields:
                assert field in record, f"Missing field: {field}"
                assert record[field] is not None, f"Null value for: {field}"
        
        # Check data constraints
        for record in records:
            assert record['defect_density'] >= 0.001
            assert record['defect_density'] <= 0.1
            assert record['data_source'] == 'synthetic'
            assert record['material'] in ['graphene', 'MoS2']
        
        # Check file creation
        assert output_path.exists()
        
        # Verify CSV content
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 10
        
        print("Synthetic data generation test passed!")

def test_seed_reproducibility():
    """Test that same seed produces same results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path1 = Path(tmpdir) / "test1.csv"
        output_path2 = Path(tmpdir) / "test2.csv"
        
        generate_synthetic_defect_data(n_samples=5, seed=42, output_path=str(output_path1))
        generate_synthetic_defect_data(n_samples=5, seed=42, output_path=str(output_path2))
        
        # Read both files
        with open(output_path1, 'r') as f1, open(output_path2, 'r') as f2:
            content1 = f1.read()
            content2 = f2.read()
        
        assert content1 == content2, "Seed reproducibility failed!"
        print("Seed reproducibility test passed!")

def run_all_tests():
    """Run all tests."""
    print("Running synthetic data generator tests...")
    test_git_hash()
    test_griffith_criterion()
    test_rule_of_mixtures()
    test_matthiessen_rule()
    test_synthetic_data_generation()
    test_seed_reproducibility()
    print("All tests passed!")

if __name__ == "__main__":
    run_all_tests()