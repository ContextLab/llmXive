"""
Integration tests for fingerprint validation (T014).
"""
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.validate_fingerprints import validate_dataset
from config import get_path_validation, ensure_directory


class TestFingerprintValidation:
    """Tests for the fingerprint validation script."""

    def test_validate_empty_dataset_fails(self, tmp_path):
        """Test that validation fails on an empty dataset."""
        # Create empty CSV
        csv_path = tmp_path / "empty_dataset.csv"
        pd.DataFrame().to_csv(csv_path, index=False)
        
        output_path = tmp_path / "result.json"
        
        result = validate_dataset(str(csv_path), str(output_path))
        
        assert result["status"] == "fail"
        assert len(result["errors"]) > 0
        assert os.path.exists(output_path)

    def test_validate_dataset_with_nulls_fails(self, tmp_path):
        """Test that validation fails when key columns have nulls."""
        # Create dataset with nulls
        data = {
            "smiles": ["CCO", None, "CCC"],
            "space_group": ["P21/c", "P21/c", None],
            "fingerprint": ["[1,0,1]", "[0,1,1]", "[1,1,0]"]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "nulls_dataset.csv"
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "result.json"
        
        result = validate_dataset(str(csv_path), str(output_path))
        
        assert result["status"] == "fail"
        assert any("null" in err.lower() for err in result["errors"])

    def test_validate_valid_dataset_passes(self, tmp_path):
        """Test that validation passes on a valid dataset."""
        # Create valid dataset
        # ECFP4 typically uses 2048 bits
        fp_2048 = "[" + ",".join(["0"] * 2048) + "]"
        
        data = {
            "smiles": ["CCO", "CCC", "CCCC"],
            "space_group": ["P21/c", "P21/c", "Pnma"],
            "lattice_a": [5.0, 6.0, 7.0],
            "lattice_b": [5.5, 6.5, 7.5],
            "lattice_c": [5.2, 6.2, 7.2],
            "alpha": [90.0, 90.0, 90.0],
            "beta": [90.0, 90.0, 90.0],
            "gamma": [90.0, 90.0, 90.0],
            "fingerprint": [fp_2048, fp_2048, fp_2048]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "valid_dataset.csv"
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "result.json"
        
        result = validate_dataset(str(csv_path), str(output_path))
        
        assert result["status"] == "pass"
        assert result["fingerprint_checks"]["dimensionality_check"] == "pass"
        assert result["fingerprint_checks"]["actual_bits"] == 2048

    def test_validate_variable_fingerprint_lengths_fails(self, tmp_path):
        """Test that validation fails when fingerprints have varying lengths."""
        data = {
            "smiles": ["CCO", "CCC", "CCCC"],
            "space_group": ["P21/c", "P21/c", "Pnma"],
            "lattice_a": [5.0, 6.0, 7.0],
            "lattice_b": [5.5, 6.5, 7.5],
            "lattice_c": [5.2, 6.2, 7.2],
            "alpha": [90.0, 90.0, 90.0],
            "beta": [90.0, 90.0, 90.0],
            "gamma": [90.0, 90.0, 90.0],
            "fingerprint": [
                "[" + ",".join(["0"] * 1024) + "]",  # 1024 bits
                "[" + ",".join(["0"] * 2048) + "]",  # 2048 bits
                "[" + ",".join(["0"] * 2048) + "]"   # 2048 bits
            ]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "variable_fp_dataset.csv"
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "result.json"
        
        result = validate_dataset(str(csv_path), str(output_path))
        
        assert result["status"] == "fail"
        assert result["fingerprint_checks"]["dimensionality_check"] == "fail"

    def test_validate_creates_output_file(self, tmp_path):
        """Test that validation creates the output JSON file."""
        data = {
            "smiles": ["CCO"],
            "space_group": ["P21/c"],
            "lattice_a": [5.0],
            "lattice_b": [5.5],
            "lattice_c": [5.2],
            "alpha": [90.0],
            "beta": [90.0],
            "gamma": [90.0],
            "fingerprint": ["[" + ",".join(["0"] * 2048) + "]"]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "test_dataset.csv"
        df.to_csv(csv_path, index=False)
        
        output_path = tmp_path / "custom_result.json"
        
        validate_dataset(str(csv_path), str(output_path))
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            result = json.load(f)
        assert "status" in result
        assert "null_checks" in result
        assert "fingerprint_checks" in result