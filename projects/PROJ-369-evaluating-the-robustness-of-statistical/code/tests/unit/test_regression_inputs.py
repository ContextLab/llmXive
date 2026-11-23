"""
Unit tests for regression input validation (T050).

Tests verify that:
1. Missing input files are detected
2. NaN/Inf values in Hurst/error_rate columns are caught
3. Dataset ID mismatches are detected
4. Validation gate is written correctly
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.analysis.regression import verify_regression_inputs, RegressionError

class TestRegressionInputValidation:
    """Test suite for verify_regression_inputs function."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directory structure for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data" / "results"
            data_dir.mkdir(parents=True)
            yield tmpdir, data_dir
    
    def test_missing_error_rates_file(self, temp_dirs):
        """Test that missing error_rates.csv raises error."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create filtered_features but not error_rates
        with open(filtered_features_path, 'w') as f:
            json.dump({"dataset1": {"hurst": 0.7}}, f)
        
        with pytest.raises(RegressionError) as exc_info:
            verify_regression_inputs(
                str(error_rates_path),
                str(filtered_features_path),
                str(output_path)
            )
        
        assert "not found" in str(exc_info.value).lower()
        
        # Verify gate was written
        assert Path(output_path).exists()
        with open(output_path, 'r') as f:
            gate = json.load(f)
        assert gate["status"] == "FAIL"
    
    def test_missing_filtered_features_file(self, temp_dirs):
        """Test that missing filtered_features.json raises error."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create error_rates but not filtered_features
        df = pd.DataFrame({
            'dataset_id': ['dataset1'],
            'hurst': [0.7],
            'error_rate': [0.05]
        })
        df.to_csv(error_rates_path, index=False)
        
        with pytest.raises(RegressionError) as exc_info:
            verify_regression_inputs(
                str(error_rates_path),
                str(filtered_features_path),
                str(output_path)
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_nan_in_hurst_column(self, temp_dirs):
        """Test that NaN values in hurst column are detected."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create data with NaN in hurst
        df = pd.DataFrame({
            'dataset_id': ['dataset1', 'dataset2'],
            'hurst': [0.7, np.nan],
            'error_rate': [0.05, 0.06]
        })
        df.to_csv(error_rates_path, index=False)
        
        with open(filtered_features_path, 'w') as f:
            json.dump({"dataset1": {}, "dataset2": {}}, f)
        
        with pytest.raises(RegressionError) as exc_info:
            verify_regression_inputs(
                str(error_rates_path),
                str(filtered_features_path),
                str(output_path)
            )
        
        assert "nan" in str(exc_info.value).lower()
    
    def test_inf_in_error_rate_column(self, temp_dirs):
        """Test that Inf values in error_rate column are detected."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create data with Inf in error_rate
        df = pd.DataFrame({
            'dataset_id': ['dataset1', 'dataset2'],
            'hurst': [0.7, 0.8],
            'error_rate': [0.05, np.inf]
        })
        df.to_csv(error_rates_path, index=False)
        
        with open(filtered_features_path, 'w') as f:
            json.dump({"dataset1": {}, "dataset2": {}}, f)
        
        with pytest.raises(RegressionError) as exc_info:
            verify_regression_inputs(
                str(error_rates_path),
                str(filtered_features_path),
                str(output_path)
            )
        
        assert "inf" in str(exc_info.value).lower()
    
    def test_dataset_id_mismatch(self, temp_dirs):
        """Test that mismatched dataset IDs are detected."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create error_rates with dataset1, dataset2
        df = pd.DataFrame({
            'dataset_id': ['dataset1', 'dataset2'],
            'hurst': [0.7, 0.8],
            'error_rate': [0.05, 0.06]
        })
        df.to_csv(error_rates_path, index=False)
        
        # Create filtered_features with dataset3, dataset4 (no overlap)
        with open(filtered_features_path, 'w') as f:
            json.dump({"dataset3": {}, "dataset4": {}}, f)
        
        with pytest.raises(RegressionError) as exc_info:
            verify_regression_inputs(
                str(error_rates_path),
                str(filtered_features_path),
                str(output_path)
            )
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_valid_input_passes(self, temp_dirs):
        """Test that valid input passes validation."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create valid error_rates
        df = pd.DataFrame({
            'dataset_id': ['dataset1', 'dataset2'],
            'hurst': [0.7, 0.8],
            'error_rate': [0.05, 0.06]
        })
        df.to_csv(error_rates_path, index=False)
        
        # Create matching filtered_features
        with open(filtered_features_path, 'w') as f:
            json.dump({
                "dataset1": {"hurst": 0.7, "features": {}},
                "dataset2": {"hurst": 0.8, "features": {}}
            }, f)
        
        # Should not raise
        success, message = verify_regression_inputs(
            str(error_rates_path),
            str(filtered_features_path),
            str(output_path)
        )
        
        assert success is True
        assert "passed" in message.lower()
        
        # Verify gate was written with PASS status
        assert Path(output_path).exists()
        with open(output_path, 'r') as f:
            gate = json.load(f)
        assert gate["status"] == "PASS"
    
    def test_missing_required_columns(self, temp_dirs):
        """Test that missing required columns are detected."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create error_rates missing 'hurst' column
        df = pd.DataFrame({
            'dataset_id': ['dataset1'],
            'error_rate': [0.05]
        })
        df.to_csv(error_rates_path, index=False)
        
        with open(filtered_features_path, 'w') as f:
            json.dump({"dataset1": {}}, f)
        
        with pytest.raises(RegressionError) as exc_info:
            verify_regression_inputs(
                str(error_rates_path),
                str(filtered_features_path),
                str(output_path)
            )
        
        assert "missing" in str(exc_info.value).lower()
    
    def test_extra_features_ignored(self, temp_dirs):
        """Test that extra dataset IDs in filtered_features are ignored with warning."""
        tmpdir, data_dir = temp_dirs
        
        error_rates_path = data_dir / "error_rates.csv"
        filtered_features_path = data_dir / "filtered_features.json"
        output_path = data_dir / "validation_gate.json"
        
        # Create error_rates with dataset1
        df = pd.DataFrame({
            'dataset_id': ['dataset1'],
            'hurst': [0.7],
            'error_rate': [0.05]
        })
        df.to_csv(error_rates_path, index=False)
        
        # Create filtered_features with extra dataset2
        with open(filtered_features_path, 'w') as f:
            json.dump({
                "dataset1": {},
                "dataset2": {}  # Extra, not in error_rates
            }, f)
        
        # Should pass but log warning
        success, message = verify_regression_inputs(
            str(error_rates_path),
            str(filtered_features_path),
            str(output_path)
        )
        
        assert success is True
        assert Path(output_path).exists()
        with open(output_path, 'r') as f:
            gate = json.load(f)
        assert gate["status"] == "PASS"