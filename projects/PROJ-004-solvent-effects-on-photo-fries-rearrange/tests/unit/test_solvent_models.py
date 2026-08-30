"""
Unit tests for T029: Solvent Model Data Generation.
Verifies partitioning logic and CSV generation.
"""
import os
import sys
import pytest
import math
from pathlib import Path
import csv
import tempfile
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.compute.solvent_models import partition_solvent_models, generate_solvent_models, write_solvent_models_csv
from code.config import get_compute_data_path

def test_partition_logic_small_n():
    """Test partitioning for small N (N < 5)."""
    # N=1: Implicit=1, Explicit=0
    i, e = partition_solvent_models(['A'])
    assert len(i) == 1
    assert len(e) == 0

    # N=2: Implicit=1, Explicit=1
    i, e = partition_solvent_models(['A', 'B'])
    assert len(i) == 1
    assert len(e) == 1

    # N=3: Implicit=2, Explicit=1
    i, e = partition_solvent_models(['A', 'B', 'C'])
    assert len(i) == 2
    assert len(e) == 1

    # N=4: Implicit=3, Explicit=1
    i, e = partition_solvent_models(['A', 'B', 'C', 'D'])
    assert len(i) == 3
    assert len(e) == 1

def test_partition_logic_large_n():
    """Test partitioning for larger N (N >= 5)."""
    # N=5: floor(4.0) = 4 Implicit, 1 Explicit (20%)
    i, e = partition_solvent_models(['A', 'B', 'C', 'D', 'E'])
    assert len(i) == 4
    assert len(e) == 1
    assert (len(e) / 5) >= 0.20

    # N=10: floor(8.0) = 8 Implicit, 2 Explicit (20%)
    i, e = partition_solvent_models(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'])
    assert len(i) == 8
    assert len(e) == 2
    assert (len(e) / 10) >= 0.20

    # N=11: floor(8.8) = 8 Implicit, 3 Explicit (~27%)
    i, e = partition_solvent_models(['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K'])
    assert len(i) == 8
    assert len(e) == 3

def test_partition_logic_minimum_explicit():
    """Test that minimum explicit count is enforced if possible."""
    # N=3: 2 Implicit, 1 Explicit. If we force min 2 explicit, we need 1 implicit.
    # The logic in generate_solvent_models says: if explicit < 2 and N >= 2, force 2 explicit.
    # Let's re-verify the logic in the code:
    # implicit = floor(3 * 0.8) = 2. explicit = 1.
    # if 1 < 2 and 3 >= 2: explicit = 2, implicit = 1.
    i, e = partition_solvent_models(['A', 'B', 'C'])
    # Wait, the function logic in the code:
    # implicit_count = floor(3 * 0.8) = 2
    # explicit_count = 1
    # if explicit_count < 2 and n_total >= 2: explicit_count = 2, implicit_count = 1
    assert len(i) == 1
    assert len(e) == 2

def test_generate_solvent_models_structure():
    """Test that generate_solvent_models returns correct structure."""
    solvents = ['benzene', 'acetone', 'water', 'ethanol', 'toluene']
    results = generate_solvent_models(solvents)
    
    assert len(results) == 5
    
    # Check keys
    required_keys = {
        'solvent_name', 'model_type', 'method', 'dielectric_constant',
        'delta_g_solv_kcal_mol', 'uncertainty_kcal_mol', 'computation_time_seconds'
    }
    
    for r in results:
        assert set(r.keys()) >= required_keys
        assert r['model_type'] in ['Implicit', 'Explicit']
        assert r['method'] in ['SMD', 'QM/MM']
        assert isinstance(r['delta_g_solv_kcal_mol'], float)
        assert isinstance(r['uncertainty_kcal_mol'], float)

def test_write_csv(tmp_path):
    """Test writing results to CSV."""
    results = [
        {
            "solvent_name": "benzene",
            "model_type": "Implicit",
            "method": "SMD",
            "dielectric_constant": 2.3,
            "delta_g_solv_kcal_mol": -12.5,
            "uncertainty_kcal_mol": 0.5,
            "computation_time_seconds": 120
        }
    ]
    
    output_file = tmp_path / "test_output.csv"
    write_solvent_models_csv(results, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 1
    assert rows[0]['solvent_name'] == 'benzene'
    assert rows[0]['model_type'] == 'Implicit'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])