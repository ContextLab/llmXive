import pytest
import json
import tempfile
from pathlib import Path
import numpy as np
from src.analysis.regression import verify_regression_inputs, RegressionError

class TestRegressionInputVerification:
    """Unit tests for T037b feature filtering and input verification logic."""

    def setup_method(self):
        """Set up temporary files for testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.error_rates_path = self.temp_dir / "error_rates.json"
        self.filtered_features_path = self.temp_dir / "filtered_features.json"
        self.hurst_path = self.temp_dir / "hurst_estimates.json"

    def test_verify_inputs_valid(self):
        """Test verification passes with valid inputs."""
        # Create valid error rates
        error_data = [
            {"dataset_id": "ds1", "hurst": 0.7, "error_rate": 0.05},
            {"dataset_id": "ds2", "hurst": 0.8, "error_rate": 0.10}
        ]
        with open(self.error_rates_path, 'w') as f:
            json.dump(error_data, f)

        # Create valid filtered features
        features_data = {
            "included_features": ["hurst"],
            "excluded_features": ["Max_ACF_Lag"]
        }
        with open(self.filtered_features_path, 'w') as f:
            json.dump(features_data, f)

        # Create valid hurst estimates
        hurst_data = [
            {"dataset_id": "ds1", "hurst": 0.7},
            {"dataset_id": "ds2", "hurst": 0.8}
        ]
        with open(self.hurst_path, 'w') as f:
            json.dump(hurst_data, f)

        result = verify_regression_inputs(
            self.error_rates_path,
            self.filtered_features_path,
            self.hurst_path
        )
        assert result['valid'] is True

    def test_verify_inputs_missing_file(self):
        """Test verification fails when a required file is missing."""
        # Create only one file
        error_data = [{"dataset_id": "ds1", "hurst": 0.7, "error_rate": 0.05}]
        with open(self.error_rates_path, 'w') as f:
            json.dump(error_data, f)

        with pytest.raises(RegressionError, match="not found"):
            verify_regression_inputs(
                self.error_rates_path,
                self.filtered_features_path, # Missing
                self.hurst_path
            )

    def test_verify_inputs_nan_values(self):
        """Test verification fails when NaN or Inf values are present."""
        # Create error rates with NaN
        error_data = [
            {"dataset_id": "ds1", "hurst": 0.7, "error_rate": float('nan')}
        ]
        with open(self.error_rates_path, 'w') as f:
            json.dump(error_data, f)

        # Create valid filtered features
        features_data = {"included_features": ["hurst"], "excluded_features": []}
        with open(self.filtered_features_path, 'w') as f:
            json.dump(features_data, f)

        with pytest.raises(RegressionError, match="NaN or Inf"):
            verify_regression_inputs(
                self.error_rates_path,
                self.filtered_features_path,
                self.hurst_path
            )

    def test_verify_inputs_id_mismatch(self):
        """Test verification fails when dataset IDs do not match."""
        # Create error rates with ds1, ds2
        error_data = [
            {"dataset_id": "ds1", "hurst": 0.7, "error_rate": 0.05},
            {"dataset_id": "ds2", "hurst": 0.8, "error_rate": 0.10}
        ]
        with open(self.error_rates_path, 'w') as f:
            json.dump(error_data, f)

        # Create valid filtered features
        features_data = {"included_features": ["hurst"], "excluded_features": []}
        with open(self.filtered_features_path, 'w') as f:
            json.dump(features_data, f)

        # Create hurst with ds1, ds3 (mismatch)
        hurst_data = [
            {"dataset_id": "ds1", "hurst": 0.7},
            {"dataset_id": "ds3", "hurst": 0.9}
        ]
        with open(self.hurst_path, 'w') as f:
            json.dump(hurst_data, f)

        with pytest.raises(RegressionError, match="Dataset ID mismatch"):
            verify_regression_inputs(
                self.error_rates_path,
                self.filtered_features_path,
                self.hurst_path
            )

    def test_verify_inputs_inf_values(self):
        """Test verification fails when Inf values are present."""
        # Create error rates with Inf
        error_data = [
            {"dataset_id": "ds1", "hurst": 0.7, "error_rate": float('inf')}
        ]
        with open(self.error_rates_path, 'w') as f:
            json.dump(error_data, f)

        # Create valid filtered features
        features_data = {"included_features": ["hurst"], "excluded_features": []}
        with open(self.filtered_features_path, 'w') as f:
            json.dump(features_data, f)

        with pytest.raises(RegressionError, match="NaN or Inf"):
            verify_regression_inputs(
                self.error_rates_path,
                self.filtered_features_path,
                self.hurst_path
            )
