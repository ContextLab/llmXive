"""
Unit tests for T015a: detect_heterogeneity module.
"""
import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the module under test
# We use a relative import pattern that works in the project structure
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from data.detect_heterogeneity import (
    DataUnavailableError,
    load_filtered_manifest,
    load_phenotype_files,
    analyze_heterogeneity,
    save_report
)

class TestLoadFilteredManifest:
    def test_load_valid_manifest(self, tmp_path):
        """Test loading a valid manifest file."""
        manifest_data = [
            {"study_id": "S001", "title": "Test Study 1"},
            {"study_id": "S002", "title": "Test Study 2"}
        ]
        manifest_file = tmp_path / "filtered_study_manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest_data, f)
        
        result = load_filtered_manifest(str(manifest_file))
        assert len(result) == 2
        assert result[0]["study_id"] == "S001"

    def test_load_missing_file(self, tmp_path):
        """Test that missing file raises DataUnavailableError."""
        with pytest.raises(DataUnavailableError):
            load_filtered_manifest(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json(self, tmp_path):
        """Test that invalid JSON raises DataUnavailableError."""
        manifest_file = tmp_path / "invalid.json"
        with open(manifest_file, 'w') as f:
            f.write("not valid json")
        
        with pytest.raises(DataUnavailableError):
            load_filtered_manifest(str(manifest_file))

class TestLoadPhenotypeFiles:
    def test_load_phenotype_file(self, tmp_path):
        """Test loading a phenotype CSV file."""
        # Create a dummy phenotype file
        phenotype_file = tmp_path / "S001_phenotype.csv"
        df = pd.DataFrame({
            "sample_id": [1, 2, 3],
            "resistance_score": [0, 1, 1]
        })
        df.to_csv(phenotype_file, index=False)
        
        result = load_phenotype_files("S001", str(tmp_path))
        assert result is not None
        assert len(result) == 3
        assert "resistance_score" in result.columns

    def test_load_missing_phenotype_file(self, tmp_path):
        """Test that missing phenotype file raises DataUnavailableError."""
        with pytest.raises(DataUnavailableError):
            load_phenotype_files("S001", str(tmp_path))

class TestAnalyzeHeterogeneity:
    def test_single_binary_method(self):
        """Test analysis of a single binary method (no heterogeneity)."""
        df = pd.DataFrame({
            "sample_id": [1, 2, 3, 4],
            "measurement_method": ["ELISA", "ELISA", "ELISA", "ELISA"],
            "resistance_score": [0, 1, 0, 1]
        })
        
        result = analyze_heterogeneity(df, "S001")
        assert result["study_id"] == "S001"
        assert result["heterogeneity_detected"] is False
        assert result["methods"] == ["ELISA"]
        assert "binary" in result["score_types"]

    def test_multiple_methods(self):
        """Test analysis of multiple measurement methods (heterogeneity detected)."""
        df = pd.DataFrame({
            "sample_id": [1, 2, 3, 4],
            "measurement_method": ["ELISA", "PCR", "ELISA", "PCR"],
            "resistance_score": [0, 1, 0, 1]
        })
        
        result = analyze_heterogeneity(df, "S001")
        assert result["heterogeneity_detected"] is True
        assert len(result["methods"]) == 2
        assert "ELISA" in result["methods"]
        assert "PCR" in result["methods"]

    def test_ordinal_scores(self):
        """Test analysis of ordinal scores."""
        df = pd.DataFrame({
            "sample_id": [1, 2, 3, 4, 5],
            "measurement_method": ["ELISA"] * 5,
            "resistance_score": [0, 1, 2, 3, 4]
        })
        
        result = analyze_heterogeneity(df, "S001")
        assert result["score_types"] == ["ordinal"]
        # Heterogeneity might be flagged if binary is expected but ordinal found
        # depending on interpretation, but we flag the type correctly.

    def test_missing_columns(self):
        """Test analysis when expected columns are missing."""
        df = pd.DataFrame({
            "sample_id": [1, 2, 3],
            "other_col": ["a", "b", "c"]
        })
        
        result = analyze_heterogeneity(df, "S001")
        # Should not crash, should handle gracefully
        assert result["study_id"] == "S001"

class TestSaveReport:
    def test_save_report(self, tmp_path):
        """Test saving the heterogeneity report."""
        results = [
            {"study_id": "S001", "heterogeneity_detected": False, "methods": ["ELISA"], "score_types": ["binary"]}
        ]
        output_file = tmp_path / "heterogeneity_report.json"
        
        save_report(results, str(output_file))
        
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
        assert len(loaded) == 1
        assert loaded[0]["study_id"] == "S001"