"""
Integration tests for the ingestion module.
"""
import pytest
import os
import sys
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest import (
    is_valid_smiles,
    validate_degradation_label,
    filter_records_with_degradation_labels
)

class TestIngestionValidation:
    
    def test_is_valid_smiles_valid(self):
        """Test valid SMILES string."""
        assert is_valid_smiles("CC(=O)Oc1ccccc1C(=O)O") is True
        
    def test_is_valid_smiles_invalid(self):
        """Test invalid SMILES string."""
        assert is_valid_smiles("invalid_smiles_123") is False
        assert is_valid_smiles("") is False
        assert is_valid_smiles(None) is False

    def test_validate_degradation_label_valid(self):
        """Test valid degradation labels."""
        assert validate_degradation_label("hydrolysis") is True
        assert validate_degradation_label("Oxidation") is True
        assert validate_degradation_label("photolysis") is True

    def test_validate_degradation_label_invalid(self):
        """Test invalid degradation labels."""
        assert validate_degradation_label("") is False
        assert validate_degradation_label(None) is False
        assert validate_degradation_label("unknown_process") is False
        assert validate_degradation_label("   ") is False

    def test_filter_records_with_degradation_labels(self):
        """Test filtering of records based on degradation labels."""
        records = [
            {"id": 1, "smiles": "CCO", "degradation_label": "hydrolysis"},
            {"id": 2, "smiles": "CCC", "degradation_label": None},
            {"id": 3, "smiles": "CCCC", "degradation_label": ""},
            {"id": 4, "smiles": "CCCCC", "degradation_label": "oxidation"},
            {"id": 5, "smiles": "CCCCCC", "degradation_label": "invalid_label"},
        ]
        
        filtered = filter_records_with_degradation_labels(records)
        
        assert len(filtered) == 2
        assert filtered[0]["id"] == 1
        assert filtered[1]["id"] == 4
