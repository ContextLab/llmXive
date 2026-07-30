import pytest
import os
import csv
from pathlib import Path
import tempfile
import shutil

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingest import (
    is_valid_smiles,
    validate_degradation_label,
    save_flagged_records,
    filter_records_with_degradation_labels
)

class TestSMILESValidation:
    """Test SMILES validation logic."""

    def test_valid_smiles(self):
        """Test that valid SMILES strings are accepted."""
        valid_smiles = [
            "CCO",  # Ethanol
            "c1ccccc1",  # Benzene
            "CC(=O)O",  # Acetic acid
            "C1CCCCC1",  # Cyclohexane
        ]
        for smiles in valid_smiles:
            assert is_valid_smiles(smiles), f"SMILES '{smiles}' should be valid"

    def test_invalid_smiles_empty(self):
        """Test that empty SMILES are rejected."""
        assert not is_valid_smiles("")
        assert not is_valid_smiles("   ")
        assert not is_valid_smiles(None)

    def test_invalid_smiles_characters(self):
        """Test that SMILES with invalid characters are rejected."""
        invalid_smiles = [
            "CC@invalid",
            "CC#123",
            "CC(ZZZ)",
        ]
        for smiles in invalid_smiles:
            assert not is_valid_smiles(smiles), f"SMILES '{smiles}' should be invalid"

class TestDegradationLabelValidation:
    """Test degradation label validation logic."""

    def test_valid_labels(self):
        """Test that known degradation labels are accepted."""
        valid_labels = [
            "hydrolysis",
            "oxidation",
            "photolysis",
            "thermal",
            "biodegradation",
            "Hydrolysis",  # Case insensitive
            "OXIDATION",
        ]
        for label in valid_labels:
            assert validate_degradation_label(label), f"Label '{label}' should be valid"

    def test_invalid_labels(self):
        """Test that unknown labels are rejected."""
        invalid_labels = [
            "unknown",
            "decomposition",
            "melting",
            "",
            None,
        ]
        for label in invalid_labels:
            assert not validate_degradation_label(label), f"Label '{label}' should be invalid"

class TestFlaggedRecords:
    """Test flagged records functionality."""

    def test_save_flagged_records_creates_file(self):
        """Test that flagged records are saved to CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "flagged.csv")
            flagged_records = [
                {"record_id": "1", "smiles": "CCO", "degradation_pathway": None},
                {"record_id": "2", "smiles": "c1ccccc1", "degradation_pathway": None},
            ]
            
            save_flagged_records(flagged_records, output_path)
            
            assert os.path.exists(output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert rows[0]["record_id"] == "1"
                assert rows[1]["record_id"] == "2"

    def test_save_flagged_records_empty(self):
        """Test that empty list doesn't create file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "flagged.csv")
            save_flagged_records([], output_path)
            assert not os.path.exists(output_path)

class TestFilterRecords:
    """Test record filtering logic."""

    def test_filter_valid_records(self):
        """Test that only records with valid degradation labels are kept."""
        records = [
            {"record_id": "1", "degradation_pathway": "hydrolysis"},
            {"record_id": "2", "degradation_pathway": "oxidation"},
            {"record_id": "3", "degradation_pathway": None},
            {"record_id": "4", "degradation_pathway": "unknown"},
            {"record_id": "5", "degradation_pathway": "photolysis"},
        ]
        
        filtered = filter_records_with_degradation_labels(records)
        
        assert len(filtered) == 3
        assert all(validate_degradation_label(r["degradation_pathway"]) for r in filtered)
        assert filtered[0]["record_id"] == "1"
        assert filtered[1]["record_id"] == "2"
        assert filtered[2]["record_id"] == "5"
