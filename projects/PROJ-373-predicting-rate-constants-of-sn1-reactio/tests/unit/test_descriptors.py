"""
Unit tests for SMILES parsing and descriptor calculation.

Tests for code/data/descriptors.py
Dependencies: T001 (project structure), T002 (requirements), T004 (config)
"""

import os
import sys
import pytest
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.descriptors import (
    compute_gasteiger_charges,
    compute_topological_indices,
    process_single_row,
    compute_descriptors_for_dataset
)
from code.utils.logger import setup_logging

# Configure logging for tests
setup_logging(level="INFO")


class TestSMILESParsing:
    """Tests for SMILES string parsing and validation."""

    def test_canonicalize_valid_smiles(self):
        """Test that valid SMILES strings are processed correctly."""
        # Simple valid SMILES
        smiles = "CCO"  # Ethanol
        result = process_single_row({"smiles": smiles}, row_index=0)
        
        assert result is not None
        assert "smiles" in result
        assert "error" not in result
        assert result["smiles"] is not None
    
    def test_empty_smiles_handling(self):
        """Test handling of empty SMILES strings."""
        smiles = ""
        result = process_single_row({"smiles": smiles}, row_index=0)
        
        assert result is not None
        assert "error" in result
        assert "empty" in result["error"].lower()
    
    def test_invalid_smiles_handling(self):
        """Test handling of invalid SMILES strings."""
        # Invalid SMILES with unmatched brackets
        smiles = "C[C"
        result = process_single_row({"smiles": smiles}, row_index=0)
        
        assert result is not None
        assert "error" in result or result.get("smiles") is None
    
    def test_complex_molecule_smiles(self):
        """Test parsing of complex molecule SMILES."""
        # Benzene with substituents
        smiles = "CC1=CC=CC=C1"  # Toluene
        result = process_single_row({"smiles": smiles}, row_index=0)
        
        assert result is not None
        assert "error" not in result
        assert result["smiles"] is not None
    
    def test_stereochemistry_smiles(self):
        """Test handling of SMILES with stereochemistry."""
        # SMILES with stereochemistry
        smiles = "C[C@H](O)C"  # Chiral center
        result = process_single_row({"smiles": smiles}, row_index=0)
        
        # Should handle without crashing
        assert result is not None
        # May or may not have error depending on RDKit's handling
        # The important thing is it doesn't crash


class TestDescriptorCalculation:
    """Tests for descriptor calculation functions."""

    def test_gasteiger_charges_basic(self):
        """Test basic Gasteiger charge calculation."""
        smiles = "CCO"  # Ethanol
        charges = compute_gasteiger_charges(smiles)
        
        assert charges is not None
        assert isinstance(charges, (list, np.ndarray))
        assert len(charges) > 0
        # Charges should be real numbers
        assert all(isinstance(c, (int, float, np.floating)) for c in charges)
    
    def test_gasteiger_charges_sum(self):
        """Test that Gasteiger charges approximately sum to molecular charge."""
        # Neutral molecule
        smiles = "CCO"  # Ethanol
        charges = compute_gasteiger_charges(smiles)
        
        charge_sum = sum(charges)
        # Should be close to 0 for neutral molecule
        assert abs(charge_sum) < 0.1
    
    def test_gasteiger_charges_unable_to_compute(self):
        """Test handling when Gasteiger charges cannot be computed."""
        # Invalid SMILES
        smiles = "INVALID"
        charges = compute_gasteiger_charges(smiles)
        
        assert charges is None
    
    def test_topological_indices_basic(self):
        """Test basic topological index calculation."""
        smiles = "CCO"  # Ethanol
        indices = compute_topological_indices(smiles)
        
        assert indices is not None
        assert isinstance(indices, dict)
        assert len(indices) > 0
    
    def test_wiener_index(self):
        """Test Wiener index calculation."""
        smiles = "CCCC"  # Butane
        indices = compute_topological_indices(smiles)
        
        assert "wiener_index" in indices
        assert indices["wiener_index"] is not None
        assert indices["wiener_index"] >= 0
    
    def test_mol_logp(self):
        """Test LogP calculation."""
        smiles = "CCO"  # Ethanol
        indices = compute_topological_indices(smiles)
        
        assert "logp" in indices
        assert indices["logp"] is not None
        assert isinstance(indices["logp"], (int, float))
    
    def test_rotatable_bonds(self):
        """Test rotatable bond count."""
        smiles = "CCCC"  # Butane has 1 rotatable bond
        indices = compute_topological_indices(smiles)
        
        assert "num_rotatable_bonds" in indices
        assert indices["num_rotatable_bonds"] >= 0
    
    def test_topological_indices_invalid(self):
        """Test handling of invalid SMILES for topological indices."""
        smiles = "INVALID"
        indices = compute_topological_indices(smiles)
        
        assert indices is None


class TestProcessSingleRow:
    """Tests for the process_single_row function."""

    def test_successful_processing(self):
        """Test successful processing of a valid row."""
        row = {
            "smiles": "CCO",
            "rate": 0.5,
            "substrate": "secondary"
        }
        result = process_single_row(row, row_index=0)
        
        assert result is not None
        assert "smiles" in result
        assert "gasteiger_charges" in result
        assert "topological_indices" in result
        assert "error" not in result
    
    def test_missing_smiles_field(self):
        """Test handling of missing SMILES field."""
        row = {
            "rate": 0.5,
            "substrate": "secondary"
        }
        result = process_single_row(row, row_index=0)
        
        assert result is not None
        assert "error" in result
    
    def test_missing_rate_field(self):
        """Test handling of missing rate field (should still process)."""
        row = {
            "smiles": "CCO",
            "substrate": "secondary"
        }
        result = process_single_row(row, row_index=0)
        
        assert result is not None
        # Should not have error for missing rate, just process descriptors
        assert "gasteiger_charges" in result
    
    def test_large_molecule(self):
        """Test processing of a larger molecule."""
        # Larger molecule
        smiles = "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O"  # Ibuprofen
        row = {"smiles": smiles}
        result = process_single_row(row, row_index=0)
        
        assert result is not None
        assert "error" not in result
        assert len(result["gasteiger_charges"]) > 5  # Ibuprofen has many atoms


class TestComputeDescriptorsForDataset:
    """Tests for batch descriptor computation."""

    def test_empty_dataset(self):
        """Test handling of empty dataset."""
        df = []  # Empty list
        results = compute_descriptors_for_dataset(df)
        
        assert results == []
    
    def test_single_row_dataset(self):
        """Test processing of single row dataset."""
        df = [{"smiles": "CCO"}]
        results = compute_descriptors_for_dataset(df)
        
        assert len(results) == 1
        assert results[0] is not None
    
    def test_multiple_rows_dataset(self):
        """Test processing of multiple row dataset."""
        df = [
            {"smiles": "CCO"},
            {"smiles": "CC"},
            {"smiles": "C"}
        ]
        results = compute_descriptors_for_dataset(df)
        
        assert len(results) == 3
        # All should have descriptors
        for result in results:
            assert result is not None
            assert "gasteiger_charges" in result
            assert "topological_indices" in result
    
    def test_mixed_valid_invalid_dataset(self):
        """Test processing of dataset with mixed valid/invalid rows."""
        df = [
            {"smiles": "CCO"},
            {"smiles": "INVALID"},
            {"smiles": "CC"}
        ]
        results = compute_descriptors_for_dataset(df)
        
        assert len(results) == 3
        # First and third should be valid, second should have error
        assert results[0] is not None and "error" not in results[0]
        assert results[1] is not None and "error" in results[1]
        assert results[2] is not None and "error" not in results[2]
    
    def test_with_pandas_dataframe(self):
        """Test processing with actual pandas DataFrame."""
        try:
            import pandas as pd
            df = pd.DataFrame([
                {"smiles": "CCO"},
                {"smiles": "CC"},
                {"smiles": "C"}
            ])
            results = compute_descriptors_for_dataset(df)
            
            assert len(results) == 3
            for result in results:
                assert result is not None
                assert "gasteiger_charges" in result
        except ImportError:
            pytest.skip("pandas not installed")

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])