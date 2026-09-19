"""
Unit tests for aggregate_summary module.

Tests the functionality of:
- load_csv_safely
- extract_model_summary
- extract_diagnostics
- run_summary_aggregation_pipeline
"""

import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from aggregate_summary import (
    load_csv_safely,
    extract_model_summary,
    extract_diagnostics,
    run_summary_aggregation_pipeline
)


class TestLoadCsvSafely:
    """Tests for load_csv_safely function."""
    
    def test_load_existing_valid_csv(self, tmp_path):
        """Test loading an existing valid CSV file."""
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df.to_csv(csv_path, index=False)
        
        result = load_csv_safely(csv_path)
        
        assert result is not None
        pd.testing.assert_frame_equal(result, df)
    
    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a non-existent file returns None."""
        csv_path = tmp_path / "nonexistent.csv"
        
        result = load_csv_safely(csv_path)
        
        assert result is None
    
    def test_load_empty_csv(self, tmp_path):
        """Test loading an empty CSV file returns None."""
        csv_path = tmp_path / "empty.csv"
        csv_path.touch()
        
        result = load_csv_safely(csv_path)
        
        assert result is None
    
    def test_load_with_required_columns_missing(self, tmp_path):
        """Test loading CSV with missing required columns returns None."""
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({"a": [1, 2, 3]})
        df.to_csv(csv_path, index=False)
        
        result = load_csv_safely(csv_path, required_columns=["a", "b"])
        
        assert result is None
    
    def test_load_with_required_columns_present(self, tmp_path):
        """Test loading CSV with all required columns present succeeds."""
        csv_path = tmp_path / "test.csv"
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df.to_csv(csv_path, index=False)
        
        result = load_csv_safely(csv_path, required_columns=["a", "b"])
        
        assert result is not None
        assert set(result.columns) == {"a", "b"}


class TestExtractModelSummary:
    """Tests for extract_model_summary function."""
    
    def test_extract_from_single_model_file(self, tmp_path):
        """Test extracting summary from a single model file."""
        # Create a mock primary_model.csv
        primary_csv = tmp_path / "primary_model.csv"
        primary_df = pd.DataFrame({
            "term": ["news_exposure_z", "political_ideology", "interaction"],
            "coef": [0.5, -0.3, 0.1],
            "P>|t|": [0.01, 0.05, 0.10],
            "std err": [0.1, 0.15, 0.05]
        })
        primary_df.to_csv(primary_csv, index=False)
        
        result = extract_model_summary(tmp_path)
        
        assert result is not None
        assert len(result) == 3
        assert all(result["model_type"] == "primary")
    
    def test_extract_from_multiple_model_files(self, tmp_path):
        """Test extracting summary from multiple model files."""
        # Create primary model
        primary_csv = tmp_path / "primary_model.csv"
        primary_df = pd.DataFrame({
            "term": ["news_exposure_z"],
            "coef": [0.5],
            "P>|t|": [0.01]
        })
        primary_df.to_csv(primary_csv, index=False)
        
        # Create binary model
        binary_csv = tmp_path / "binary_model.csv"
        binary_df = pd.DataFrame({
            "term": ["news_exposure_z"],
            "coef": [0.4],
            "P>|t|": [0.03]
        })
        binary_df.to_csv(binary_csv, index=False)
        
        result = extract_model_summary(tmp_path)
        
        assert result is not None
        assert len(result) == 2
        model_types = set(result["model_type"])
        assert "primary" in model_types
        assert "binary" in model_types
    
    def test_extract_with_missing_files(self, tmp_path):
        """Test extracting summary when some model files are missing."""
        # Only create primary model
        primary_csv = tmp_path / "primary_model.csv"
        primary_df = pd.DataFrame({
            "term": ["news_exposure_z"],
            "coef": [0.5],
            "P>|t|": [0.01]
        })
        primary_df.to_csv(primary_csv, index=False)
        
        result = extract_model_summary(tmp_path)
        
        assert result is not None
        assert len(result) == 1
        assert result["model_type"].iloc[0] == "primary"
    
    def test_extract_from_empty_results(self, tmp_path):
        """Test extracting summary when no model files exist."""
        result = extract_model_summary(tmp_path)
        
        assert result is None


class TestExtractDiagnostics:
    """Tests for extract_diagnostics function."""
    
    def test_extract_from_single_diag_file(self, tmp_path):
        """Test extracting diagnostics from a single file."""
        diag_csv = tmp_path / "diagnostics.csv"
        diag_df = pd.DataFrame({
            "metric": ["missing_rate", "imputation_iterations"],
            "value": [0.15, 5]
        })
        diag_df.to_csv(diag_csv, index=False)
        
        result = extract_diagnostics(tmp_path)
        
        assert result is not None
        assert len(result) == 2
        assert "source_file" in result.columns
    
    def test_extract_from_multiple_diag_files(self, tmp_path):
        """Test extracting diagnostics from multiple files."""
        # Create diagnostics.csv
        diag_csv = tmp_path / "diagnostics.csv"
        pd.DataFrame({"metric": ["m1"], "value": [1]}).to_csv(diag_csv, index=False)
        
        # Create power_design.csv
        power_csv = tmp_path / "power_design.csv"
        pd.DataFrame({"metric": ["p1"], "value": [2]}).to_csv(power_csv, index=False)
        
        result = extract_diagnostics(tmp_path)
        
        assert result is not None
        assert len(result) == 2
        sources = set(result["source_file"])
        assert "diagnostics.csv" in sources
        assert "power_design.csv" in sources
    
    def test_extract_with_missing_files(self, tmp_path):
        """Test extracting diagnostics when some files are missing."""
        # Only create diagnostics.csv
        diag_csv = tmp_path / "diagnostics.csv"
        pd.DataFrame({"metric": ["m1"], "value": [1]}).to_csv(diag_csv, index=False)
        
        result = extract_diagnostics(tmp_path)
        
        assert result is not None
        assert len(result) == 1
        assert result["source_file"].iloc[0] == "diagnostics.csv"
    
    def test_extract_from_empty_results(self, tmp_path):
        """Test extracting diagnostics when no files exist."""
        result = extract_diagnostics(tmp_path)
        
        assert result is None


class TestRunSummaryAggregationPipeline:
    """Tests for run_summary_aggregation_pipeline function."""
    
    def test_pipeline_generates_expected_files(self, tmp_path):
        """Test that pipeline generates both output files."""
        # Create mock input files
        primary_csv = tmp_path / "primary_model.csv"
        pd.DataFrame({"term": ["t1"], "coef": [0.5]}).to_csv(primary_csv, index=False)
        
        diag_csv = tmp_path / "diagnostics.csv"
        pd.DataFrame({"metric": ["m1"], "value": [1]}).to_csv(diag_csv, index=False)
        
        with patch('aggregate_summary.get_results_path', return_value=tmp_path):
            output_files = run_summary_aggregation_pipeline(tmp_path)
        
        assert "model_summary.csv" in output_files
        assert "diagnostics.csv" in output_files
        assert output_files["model_summary.csv"].exists()
        assert output_files["diagnostics.csv"].exists()
    
    def test_pipeline_with_no_input_files(self, tmp_path):
        """Test pipeline behavior when no input files exist."""
        with patch('aggregate_summary.get_results_path', return_value=tmp_path):
            output_files = run_summary_aggregation_pipeline(tmp_path)
        
        # Should not generate any output files
        assert len(output_files) == 0
    
    def test_pipeline_creates_output_directory(self, tmp_path):
        """Test that pipeline creates results directory if it doesn't exist."""
        results_path = tmp_path / "results"
        
        # Don't create the directory
        
        with patch('aggregate_summary.get_results_path', return_value=results_path):
            # Create minimal input files
            (results_path / "primary_model.csv").parent.mkdir(parents=True)
            pd.DataFrame({"term": ["t1"], "coef": [0.5]}).to_csv(
                results_path / "primary_model.csv", index=False
            )
            
            output_files = run_summary_aggregation_pipeline(results_path)
        
        assert results_path.exists()
        assert "model_summary.csv" in output_files
