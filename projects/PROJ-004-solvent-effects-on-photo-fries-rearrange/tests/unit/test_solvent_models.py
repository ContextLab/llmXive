"""
Unit tests for code/data/compute/solvent_models.py (T029)
"""
import pytest
import math
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.compute.solvent_models import partition_solvent_models, generate_solvent_models, _fetch_dft_solvation_energy_implicit

class TestPartitionSolventModels:
    """Tests for the partitioning logic (FR-005 compliance)."""

    def test_partition_small_set(self):
        """Test partitioning with N=5 (minimum for 20% rule)."""
        solvents = ["A", "B", "C", "D", "E"]
        implicit, explicit = partition_solvent_models(solvents, seed=42)
        
        # 5 * 0.8 = 4.0 -> floor = 4 implicit
        # Remainder = 1 explicit
        # 1/5 = 20% -> satisfies >= 20%
        assert len(implicit) == 4
        assert len(explicit) == 1
        assert len(implicit) + len(explicit) == 5

    def test_partition_ensures_explicit_minimum(self):
        """Verify that explicit count is at least ceil(N*0.2) for N >= 5."""
        # Test with N=10
        # floor(10*0.8) = 8 implicit, 2 explicit (20%) -> OK
        # Test with N=12
        # floor(12*0.8) = 9 implicit, 3 explicit (25%) -> OK
        # Test with N=13
        # floor(13*0.8) = 10 implicit, 3 explicit (23%) -> OK
        
        for n in range(5, 20):
            solvents = [f"S{i}" for i in range(n)]
            implicit, explicit = partition_solvent_models(solvents, seed=42)
            
            total = len(implicit) + len(explicit)
            assert total == n, f"Total count mismatch for N={n}"
            
            min_explicit = math.ceil(n * 0.2)
            assert len(explicit) >= min_explicit, f"Explicit count {len(explicit)} < {min_explicit} for N={n}"

    def test_partition_empty_list(self):
        """Test with empty list."""
        implicit, explicit = partition_solvent_models([], seed=42)
        assert len(implicit) == 0
        assert len(explicit) == 0

    def test_partition_deterministic(self):
        """Test that same seed yields same partition."""
        solvents = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
        
        imp1, exp1 = partition_solvent_models(solvents, seed=123)
        imp2, exp2 = partition_solvent_models(solvents, seed=123)
        
        assert imp1 == imp2
        assert exp1 == exp2

class TestGenerateSolventModels:
    """Tests for the model generation logic."""

    @patch('data.compute.solvent_models.get_all_solvents')
    @patch('data.compute.solvent_models.get_solvent_properties')
    def test_generate_uses_all_solvents_if_none_provided(self, mock_get_props, mock_get_all):
        """Test that generate_solvent_models uses all solvents if list is None."""
        mock_get_all.return_value = ["Acetone", "Benzene"]
        mock_get_props.side_effect = lambda name: {
            "name": name,
            "dielectric_constant": 20.0 if name == "Acetone" else 2.3
        }
        
        results = generate_solvent_models(solvent_names=None, seed=42)
        
        assert len(results) == 2
        solvents_in_results = [r['solvent_name'] for r in results]
        assert "Acetone" in solvents_in_results
        assert "Benzene" in solvents_in_results

    @patch('data.compute.solvent_models.get_solvent_properties')
    def test_generate_skips_missing_properties(self, mock_get_props):
        """Test that missing solvent properties are skipped."""
        mock_get_props.return_value = None
        
        results = generate_solvent_models(["MissingSolvent"], seed=42)
        
        assert len(results) == 0

    def test_implicit_energy_physical_trend(self):
        """Test that implicit energy correlates with dielectric constant."""
        # Low dielectric -> less negative energy
        e_low = _fetch_dft_solvation_energy_implicit("LowE", 2.0)
        # High dielectric -> more negative energy
        e_high = _fetch_dft_solvation_energy_implicit("HighE", 80.0)
        
        # The function implements: E ~ - (eps-1)/(2eps+1)
        # As eps increases, the factor approaches 0.5, so energy becomes more negative.
        assert e_high < e_low, "High dielectric should yield more negative solvation energy"