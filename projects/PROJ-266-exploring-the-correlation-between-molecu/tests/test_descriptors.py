"""
Unit tests for conformer generation and variance calculation in code/data/descriptors.py.
Implements T017.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config import set_seed
from data.descriptors import (
    generate_conformers,
    calculate_variance_metrics,
    flag_outliers,
    process_molecules
)

# Set a fixed seed for deterministic test results
set_seed(42)

# Sample SMILES for testing
# Benzene: rigid, expected low variance
SMILES_BENZENE = "c1ccccc1"
# Butane: flexible, expected higher variance
SMILES_BUTANE = "CCCC"
# Ethanol: small, flexible
SMILES_ETHANOL = "CCO"

class TestConformerGeneration:
    """Tests for generate_conformers function."""

    def test_generate_conformers_benzene(self):
        """Test conformer generation for a rigid molecule (benzene)."""
        smiles_list = [SMILES_BENZENE]
        # Request 20 conformers as per DEV-001
        result = generate_conformers(smiles_list, num_conformers=20)

        assert len(result) == 1
        assert "smiles" in result[0]
        assert "conformers" in result[0]
        assert "success" in result[0]
        assert result[0]["success"] is True
        # Should generate 20 conformers
        assert len(result[0]["conformers"]) == 20

    def test_generate_conformers_butane(self):
        """Test conformer generation for a flexible molecule (butane)."""
        smiles_list = [SMILES_BUTANE]
        result = generate_conformers(smiles_list, num_conformers=20)

        assert len(result) == 1
        assert result[0]["success"] is True
        assert len(result[0]["conformers"]) == 20

    def test_generate_conformers_invalid_smiles(self):
        """Test conformer generation with invalid SMILES."""
        smiles_list = ["invalid_smiles_string"]
        result = generate_conformers(smiles_list, num_conformers=20)

        assert len(result) == 1
        assert result[0]["success"] is False
        assert "error" in result[0]

    def test_generate_conformers_empty_list(self):
        """Test conformer generation with empty list."""
        result = generate_conformers([], num_conformers=20)
        assert len(result) == 0

    def test_generate_conformers_multiple_molecules(self):
        """Test conformer generation for multiple molecules."""
        smiles_list = [SMILES_BENZENE, SMILES_BUTANE, SMILES_ETHANOL]
        result = generate_conformers(smiles_list, num_conformers=20)

        assert len(result) == 3
        assert all(r["success"] for r in result)
        assert all(len(r["conformers"]) == 20 for r in result)


class TestVarianceCalculation:
    """Tests for calculate_variance_metrics function."""

    def test_variance_calculation_structure(self):
        """Test that variance metrics are calculated correctly."""
        # Create a mock conformer result
        mock_data = [
            {
                "smiles": SMILES_BUTANE,
                "conformers": generate_conformers([SMILES_BUTANE], 20)[0]["conformers"],
                "success": True
            }
        ]
        
        result = calculate_variance_metrics(mock_data)

        assert len(result) == 1
        assert "smiles" in result[0]
        assert "bond_variance" in result[0]
        assert "angle_variance" in result[0]
        assert "dihedral_variance" in result[0]
        
        # Variance should be non-negative
        assert result[0]["bond_variance"] >= 0
        assert result[0]["angle_variance"] >= 0
        assert result[0]["dihedral_variance"] >= 0

    def test_variance_units(self):
        """Test that variance is in expected units (rad^2 for dihedral)."""
        mock_data = [
            {
                "smiles": SMILES_BUTANE,
                "conformers": generate_conformers([SMILES_BUTANE], 20)[0]["conformers"],
                "success": True
            }
        ]
        
        result = calculate_variance_metrics(mock_data)
        
        # Dihedral variance should be in rad^2 (typically small values)
        dihedral_var = result[0]["dihedral_variance"]
        # Reasonable range for dihedral variance in rad^2
        assert 0 <= dihedral_var < 100, f"Dihedral variance {dihedral_var} seems unreasonably large"

    def test_variance_rigid_vs_flexible(self):
        """Test that rigid molecules have lower variance than flexible ones."""
        benzene_data = generate_conformers([SMILES_BENZENE], 20)
        butane_data = generate_conformers([SMILES_BUTANE], 20)
        
        benzene_var = calculate_variance_metrics(benzene_data)[0]
        butane_var = calculate_variance_metrics(butane_data)[0]
        
        # Benzene should have lower dihedral variance than butane
        assert benzene_var["dihedral_variance"] < butane_var["dihedral_variance"], \
            "Rigid benzene should have lower dihedral variance than flexible butane"


class TestOutlierFlagging:
    """Tests for flag_outliers function."""

    def test_outlier_flagging_basic(self):
        """Test basic outlier flagging logic."""
        # Create synthetic data with clear outliers
        test_data = pd.DataFrame({
            "dihedral_variance": [1.0, 1.1, 1.2, 1.3, 10.0, 1.05]  # 10.0 is an outlier
        })
        
        result = flag_outliers(test_data)
        
        assert "is_outlier" in result.columns
        # The outlier (10.0) should be flagged
        outlier_count = result["is_outlier"].sum()
        assert outlier_count >= 1, "Expected at least one outlier to be flagged"

    def test_outlier_flagging_no_outliers(self):
        """Test flagging when no outliers exist."""
        test_data = pd.DataFrame({
            "dihedral_variance": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
        })
        
        result = flag_outliers(test_data)
        
        assert "is_outlier" in result.columns
        # With such a tight distribution, likely no outliers
        # But we just verify the function runs without error

    def test_outlier_flagging_empty_dataframe(self):
        """Test flagging on empty dataframe."""
        test_data = pd.DataFrame(columns=["dihedral_variance"])
        result = flag_outliers(test_data)
        
        assert "is_outlier" in result.columns
        assert len(result) == 0


class TestProcessMolecules:
    """Tests for the full process_molecules pipeline."""

    def test_full_pipeline(self):
        """Test the complete molecule processing pipeline."""
        smiles_list = [SMILES_BENZENE, SMILES_BUTANE, SMILES_ETHANOL]
        
        result = process_molecules(smiles_list, num_conformers=20)
        
        assert len(result) == 3
        # All should succeed
        assert all(r["success"] for r in result)
        # Should have variance metrics
        assert all("dihedral_variance" in r for r in result)
        assert all("bond_variance" in r for r in result)
        assert all("angle_variance" in r for r in result)

    def test_full_pipeline_with_failure(self):
        """Test pipeline with one invalid SMILES."""
        smiles_list = [SMILES_BENZENE, "invalid", SMILES_BUTANE]
        
        result = process_molecules(smiles_list, num_conformers=20)
        
        assert len(result) == 3
        # First and third should succeed, second should fail
        assert result[0]["success"] is True
        assert result[1]["success"] is False
        assert result[2]["success"] is True

    def test_pipeline_variance_consistency(self):
        """Test that variance calculations are consistent across runs."""
        set_seed(42)
        smiles_list = [SMILES_BUTANE]
        
        result1 = process_molecules(smiles_list, num_conformers=20)
        set_seed(42)
        result2 = process_molecules(smiles_list, num_conformers=20)
        
        # With same seed, results should be identical
        assert result1[0]["dihedral_variance"] == result2[0]["dihedral_variance"]
        assert result1[0]["bond_variance"] == result2[0]["bond_variance"]
        assert result1[0]["angle_variance"] == result2[0]["angle_variance"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
