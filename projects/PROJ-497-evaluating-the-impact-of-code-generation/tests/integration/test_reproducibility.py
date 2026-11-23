"""
Integration tests for reproducibility verification (Task T037)

These tests verify that the pipeline produces identical results when run twice
with the same random seed.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import pandas as pd
import numpy as np

# Import the module to test
import code.reproducibility_check as repro_module


class TestReproducibilityChecks:
    """Test suite for reproducibility verification functions."""

    def test_compare_float_arrays_identical(self):
        """Test comparison of identical float arrays."""
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([1.0, 2.0, 3.0])
        
        result, max_diff = repro_module.compare_float_arrays(arr1, arr2, tolerance=1e-6)
        assert result is True
        assert max_diff == 0.0

    def test_compare_float_arrays_within_tolerance(self):
        """Test comparison of arrays within tolerance."""
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([1.0 + 1e-7, 2.0 + 1e-7, 3.0 + 1e-7])
        
        result, max_diff = repro_module.compare_float_arrays(arr1, arr2, tolerance=1e-6)
        assert result is True
        assert max_diff < 1e-6

    def test_compare_float_arrays_exceeds_tolerance(self):
        """Test comparison of arrays exceeding tolerance."""
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([1.0 + 1e-5, 2.0 + 1e-5, 3.0 + 1e-5])
        
        result, max_diff = repro_module.compare_float_arrays(arr1, arr2, tolerance=1e-6)
        assert result is False
        assert max_diff > 1e-6

    def test_compare_float_arrays_shape_mismatch(self):
        """Test comparison of arrays with different shapes."""
        arr1 = np.array([1.0, 2.0, 3.0])
        arr2 = np.array([1.0, 2.0])
        
        result, max_diff = repro_module.compare_float_arrays(arr1, arr2, tolerance=1e-6)
        assert result is False
        assert max_diff == float('inf')

    def test_compare_csv_files_identical(self, tmp_path):
        """Test comparison of identical CSV files."""
        # Create test CSV files
        df = pd.DataFrame({
            'col1': [1.0, 2.0, 3.0],
            'col2': ['a', 'b', 'c']
        })
        
        file1 = tmp_path / "test1.csv"
        file2 = tmp_path / "test2.csv"
        df.to_csv(file1, index=False)
        df.to_csv(file2, index=False)
        
        result, details = repro_module.compare_csv_files(file1, file2, tolerance=1e-6)
        assert result is True
        assert "error" not in details

    def test_compare_csv_files_float_difference(self, tmp_path):
        """Test comparison of CSV files with small float differences."""
        df1 = pd.DataFrame({
            'col1': [1.0, 2.0, 3.0],
            'col2': [4.0, 5.0, 6.0]
        })
        
        df2 = pd.DataFrame({
            'col1': [1.0 + 1e-7, 2.0 + 1e-7, 3.0 + 1e-7],
            'col2': [4.0 + 1e-7, 5.0 + 1e-7, 6.0 + 1e-7]
        })
        
        file1 = tmp_path / "test1.csv"
        file2 = tmp_path / "test2.csv"
        df1.to_csv(file1, index=False)
        df2.to_csv(file2, index=False)
        
        result, details = repro_module.compare_csv_files(file1, file2, tolerance=1e-6)
        assert result is True
        assert details["max_diff"] < 1e-6

    def test_compare_csv_files_shape_mismatch(self, tmp_path):
        """Test comparison of CSV files with different shapes."""
        df1 = pd.DataFrame({
            'col1': [1.0, 2.0, 3.0]
        })
        
        df2 = pd.DataFrame({
            'col1': [1.0, 2.0]
        })
        
        file1 = tmp_path / "test1.csv"
        file2 = tmp_path / "test2.csv"
        df1.to_csv(file1, index=False)
        df2.to_csv(file2, index=False)
        
        result, details = repro_module.compare_csv_files(file1, file2, tolerance=1e-6)
        assert result is False
        assert "error" in details
        assert details["error"] == "Shape mismatch"

    def test_compare_json_files_identical(self, tmp_path):
        """Test comparison of identical JSON files."""
        data = {
            "key1": 1.0,
            "key2": [2.0, 3.0, 4.0],
            "nested": {
                "value": 5.0
            }
        }
        
        file1 = tmp_path / "test1.json"
        file2 = tmp_path / "test2.json"
        
        with open(file1, 'w') as f:
            json.dump(data, f)
        with open(file2, 'w') as f:
            json.dump(data, f)
        
        result, details = repro_module.compare_json_files(file1, file2, tolerance=1e-6)
        assert result is True
        assert "issues" not in details or len(details.get("issues", [])) == 0

    def test_compare_json_files_float_difference(self, tmp_path):
        """Test comparison of JSON files with small float differences."""
        data1 = {
            "key1": 1.0,
            "key2": [2.0, 3.0, 4.0]
        }
        
        data2 = {
            "key1": 1.0 + 1e-7,
            "key2": [2.0 + 1e-7, 3.0 + 1e-7, 4.0 + 1e-7]
        }
        
        file1 = tmp_path / "test1.json"
        file2 = tmp_path / "test2.json"
        
        with open(file1, 'w') as f:
            json.dump(data1, f)
        with open(file2, 'w') as f:
            json.dump(data2, f)
        
        result, details = repro_module.compare_json_files(file1, file2, tolerance=1e-6)
        assert result is True
        assert len(details.get("issues", [])) == 0

    def test_compare_json_files_large_difference(self, tmp_path):
        """Test comparison of JSON files with large float differences."""
        data1 = {
            "key1": 1.0
        }
        
        data2 = {
            "key1": 1.0 + 1e-5
        }
        
        file1 = tmp_path / "test1.json"
        file2 = tmp_path / "test2.json"
        
        with open(file1, 'w') as f:
            json.dump(data1, f)
        with open(file2, 'w') as f:
            json.dump(data2, f)
        
        result, details = repro_module.compare_json_files(file1, file2, tolerance=1e-6)
        assert result is False
        assert len(details.get("issues", [])) > 0

    def test_compare_json_files_structure_mismatch(self, tmp_path):
        """Test comparison of JSON files with different structure."""
        data1 = {
            "key1": 1.0,
            "key2": 2.0
        }
        
        data2 = {
            "key1": 1.0
        }
        
        file1 = tmp_path / "test1.json"
        file2 = tmp_path / "test2.json"
        
        with open(file1, 'w') as f:
            json.dump(data1, f)
        with open(file2, 'w') as f:
            json.dump(data2, f)
        
        result, details = repro_module.compare_json_files(file1, file2, tolerance=1e-6)
        assert result is False
        assert len(details.get("issues", [])) > 0

    def test_calculate_file_hash(self, tmp_path):
        """Test file hash calculation."""
        test_file = tmp_path / "test.txt"
        content = "test content"
        test_file.write_text(content)
        
        hash1 = repro_module.calculate_file_hash(test_file)
        hash2 = repro_module.calculate_file_hash(test_file)
        
        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 == hash2

    def test_calculate_file_hash_different_content(self, tmp_path):
        """Test that different content produces different hashes."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        
        file1.write_text("content1")
        file2.write_text("content2")
        
        hash1 = repro_module.calculate_file_hash(file1)
        hash2 = repro_module.calculate_file_hash(file2)
        
        assert hash1 != hash2

class TestReproducibilityIntegration:
    """Integration tests for the full reproducibility check workflow."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "seed": 42,
            "models": ["starcoder", "codegen"],
            "benchmarks": ["human_eval", "mbpp"]
        }

    @pytest.fixture
    def mock_data_dirs(self, tmp_path):
        """Create mock data directories."""
        data_dirs = {
            "generated": tmp_path / "generated",
            "processed": tmp_path / "processed",
            "human": tmp_path / "human"
        }
        
        for dir_path in data_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        return data_dirs

    def test_end_to_end_reproducibility_check(self, mock_data_dirs, tmp_path):
        """Test the end-to-end reproducibility check workflow."""
        # Create mock output files for run1
        run1_dir = tmp_path / "run1" / "data" / "processed"
        run1_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock CSV with identical data
        df = pd.DataFrame({
            'task_id': ['task1', 'task2'],
            'source_type': ['human', 'llm'],
            'vulnerability_count': [5.0, 10.0],
            'convergence_status': ['converged', 'converged']
        })
        df.to_csv(run1_dir / "aggregated_analysis_dataset.csv", index=False)
        
        # Create mock JSON
        json_data = {
            "fpr": {"human": 0.1, "llm": 0.15},
            "metrics": {
                "precision": 0.85,
                "recall": 0.90
            }
        }
        with open(run1_dir / "fpr_metrics.json", 'w') as f:
            json.dump(json_data, f)
        
        # Create identical files for run2
        run2_dir = tmp_path / "run2" / "data" / "processed"
        run2_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(run2_dir / "aggregated_analysis_dataset.csv", index=False)
        with open(run2_dir / "fpr_metrics.json", 'w') as f:
            json.dump(json_data, f)
        
        # Run comparison
        csv_file1 = run1_dir / "aggregated_analysis_dataset.csv"
        csv_file2 = run2_dir / "aggregated_analysis_dataset.csv"
        json_file1 = run1_dir / "fpr_metrics.json"
        json_file2 = run2_dir / "fpr_metrics.json"
        
        csv_valid, csv_details = repro_module.compare_csv_files(csv_file1, csv_file2, tolerance=1e-6)
        json_valid, json_details = repro_module.compare_json_files(json_file1, json_file2, tolerance=1e-6)
        
        assert csv_valid is True
        assert json_valid is True
        assert "error" not in csv_details
        assert len(json_details.get("issues", [])) == 0

    def test_reproducibility_check_with_nan_values(self, tmp_path):
        """Test reproducibility check handles NaN values correctly."""
        df1 = pd.DataFrame({
            'col1': [1.0, np.nan, 3.0],
            'col2': [4.0, 5.0, np.nan]
        })
        
        df2 = pd.DataFrame({
            'col1': [1.0, np.nan, 3.0],
            'col2': [4.0, 5.0, np.nan]
        })
        
        file1 = tmp_path / "test1.csv"
        file2 = tmp_path / "test2.csv"
        df1.to_csv(file1, index=False)
        df2.to_csv(file2, index=False)
        
        result, details = repro_module.compare_csv_files(file1, file2, tolerance=1e-6)
        assert result is True
        assert "error" not in details

    def test_reproducibility_check_with_different_nan_positions(self, tmp_path):
        """Test reproducibility check detects different NaN positions."""
        df1 = pd.DataFrame({
            'col1': [1.0, np.nan, 3.0]
        })
        
        df2 = pd.DataFrame({
            'col1': [np.nan, 2.0, 3.0]
        })
        
        file1 = tmp_path / "test1.csv"
        file2 = tmp_path / "test2.csv"
        df1.to_csv(file1, index=False)
        df2.to_csv(file2, index=False)
        
        result, details = repro_module.compare_csv_files(file1, file2, tolerance=1e-6)
        # This should fail because NaN positions are different
        assert result is False
        assert "error" not in details  # Shape matches, but values differ