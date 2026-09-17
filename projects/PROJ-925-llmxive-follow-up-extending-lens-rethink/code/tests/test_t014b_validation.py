"""
Tests for Task T014b: Preliminary Validation of Linguistic Uncertainty Proxy.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.validate_features import validate_linguistic_uncertainty_proxy
from code.utils.errors import DataSchemaError

class TestT014bValidation:
    """Tests for the validation script logic."""

    @pytest.fixture
    def mock_raw_data(self):
        """Create a temporary parquet file with mock data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            data = {
                "human_rating": [4.5, 3.2, 5.0, 2.1, 4.8],
                "caption": [
                    "A cat sitting on a mat",
                    "A dog running in the park",
                    "A bird flying in the sky",
                    "A fish swimming in the water",
                    "A horse galloping on the grass"
                ]
            }
            df = pd.DataFrame(data)
            parquet_path = tmp_path / "pick-a-pic.parquet"
            df.to_parquet(parquet_path)
            yield parquet_path

    @patch('code.data.validate_features.compute_linguistic_uncertainty_proxy')
    def test_validation_success(self, mock_compute, mock_raw_data):
        """Test successful validation with mock data."""
        # Mock the function to return deterministic values
        mock_compute.side_effect = [1.2, 1.5, 1.8, 1.1, 1.4]

        output_path = Path(tempfile.mktemp(suffix=".json"))
        
        try:
            report = validate_linguistic_uncertainty_proxy(
                input_path=mock_raw_data,
                output_path=output_path,
                sample_size=5
            )

            assert report["total_samples"] == 5
            assert report["successful_calculations"] == 5
            assert report["failed_calculations"] == 0
            assert report["mean_value"] > 0.0
            assert os.path.exists(output_path)

            # Verify JSON content
            with open(output_path, 'r') as f:
                saved_report = json.load(f)
            assert saved_report["total_samples"] == 5

        finally:
            if output_path.exists():
                output_path.unlink()

    @patch('code.data.validate_features.compute_linguistic_uncertainty_proxy')
    def test_validation_with_failures(self, mock_compute, mock_raw_data):
        """Test validation with some failed calculations."""
        # Mock function to return None for some inputs (simulating failure)
        mock_compute.side_effect = [1.2, None, 1.8, None, 1.4]

        output_path = Path(tempfile.mktemp(suffix=".json"))
        
        try:
            report = validate_linguistic_uncertainty_proxy(
                input_path=mock_raw_data,
                output_path=output_path,
                sample_size=5
            )

            assert report["total_samples"] == 5
            assert report["successful_calculations"] == 3
            assert report["failed_calculations"] == 2
            assert report["timeouts"] + report["bert_failures"] == 2

        finally:
            if output_path.exists():
                output_path.unlink()

    def test_missing_raw_data(self, mock_raw_data):
        """Test that validation fails loudly if raw data is missing."""
        # Create a path that doesn't exist
        missing_path = Path("/nonexistent/path/pick-a-pic.parquet")
        output_path = Path(tempfile.mktemp(suffix=".json"))

        with pytest.raises(DataSchemaError) as exc_info:
            validate_linguistic_uncertainty_proxy(
                input_path=missing_path,
                output_path=output_path
            )

        assert "Raw data file not found" in str(exc_info.value)

    def test_missing_human_rating_column(self, tmp_path):
        """Test validation fails if human_rating column is missing."""
        # Create a parquet file without human_rating
        data = {
            "caption": ["A cat", "A dog"],
            "other_col": [1, 2]
        }
        df = pd.DataFrame(data)
        parquet_path = tmp_path / "no_rating.parquet"
        df.to_parquet(parquet_path)

        output_path = Path(tempfile.mktemp(suffix=".json"))

        with pytest.raises(DataSchemaError) as exc_info:
            validate_linguistic_uncertainty_proxy(
                input_path=parquet_path,
                output_path=output_path
            )

        assert "Missing required dataset or column" in str(exc_info.value)

    @patch('code.data.validate_features.compute_linguistic_uncertainty_proxy')
    def test_empty_captions_handled(self, mock_compute, mock_raw_data):
        """Test that empty captions are excluded and logged."""
        # Add an empty caption to the mock data
        data = {
            "human_rating": [4.5, 3.2, 5.0],
            "caption": ["A cat", "", "A bird"]
        }
        df = pd.DataFrame(data)
        parquet_path = Path(mock_raw_data).parent / "with_empty.parquet"
        df.to_parquet(parquet_path)

        mock_compute.side_effect = [1.2, 1.5]

        output_path = Path(tempfile.mktemp(suffix=".json"))
        
        try:
            report = validate_linguistic_uncertainty_proxy(
                input_path=parquet_path,
                output_path=output_path,
                sample_size=3
            )

            # Should have 3 samples, 1 failed (empty), 2 successful
            assert report["total_samples"] == 3
            assert report["successful_calculations"] == 2
            assert report["failed_calculations"] == 1
            assert "EMPTY_CAPTION" in report["exclusion_reasons"]

        finally:
            if output_path.exists():
                output_path.unlink()
            if parquet_path.exists():
                parquet_path.unlink()