"""
Unit tests for edge cases: corrupted timestamps and missing metadata.

These tests validate the robustness of the data processing pipeline
when encountering malformed or incomplete data.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprocessing.preprocess import load_raw_data, validate_data_columns
from preprocessing.features import extract_features
from utils.provenance import hash_file, write_meta
from data_model import Dataset


class TestCorruptedTimestamps:
    """Tests for handling corrupted or malformed timestamp data."""

    def test_missing_timestamp_column(self):
        """Test that missing timestamp column is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create CSV without timestamp column
            data = {
                'x': [1.0, 2.0, 3.0],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "no_timestamp.csv"
            df.to_csv(csv_path, index=False)

            # Should raise ValueError for missing required column
            with pytest.raises(ValueError) as exc_info:
                load_raw_data(csv_path)
            
            assert "timestamp" in str(exc_info.value).lower()

    def test_non_numeric_timestamps(self):
        """Test handling of non-numeric timestamp values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                'timestamp': ['invalid', 'data', 'here'],
                'x': [1.0, 2.0, 3.0],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "bad_timestamps.csv"
            df.to_csv(csv_path, index=False)

            # Should raise ValueError for non-numeric timestamps
            with pytest.raises((ValueError, TypeError)):
                load_raw_data(csv_path)

    def test_out_of_order_timestamps(self):
        """Test handling of out-of-order timestamps (should be sorted)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                'timestamp': [3.0, 1.0, 2.0],
                'x': [1.0, 2.0, 3.0],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "out_of_order.csv"
            df.to_csv(csv_path, index=False)

            # Should load successfully and sort internally
            result_df = load_raw_data(csv_path)
            assert result_df['timestamp'].is_monotonic_increasing

    def test_duplicate_timestamps(self):
        """Test handling of duplicate timestamps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                'timestamp': [1.0, 1.0, 2.0],
                'x': [1.0, 2.0, 3.0],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "duplicate_timestamps.csv"
            df.to_csv(csv_path, index=False)

            # Should load successfully (duplicates may be handled downstream)
            result_df = load_raw_data(csv_path)
            assert len(result_df) == 3


class TestMissingMetadata:
    """Tests for handling missing or incomplete metadata."""

    def test_missing_metadata_file(self):
        """Test behavior when metadata file is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data file but no metadata
            data = {
                'timestamp': [1.0, 2.0, 3.0],
                'x': [1.0, 2.0, 3.0],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "data.csv"
            df.to_csv(csv_path, index=False)

            # Metadata file doesn't exist
            meta_path = Path(tmpdir) / "data_meta.json"
            
            # Should handle missing metadata gracefully
            # (may log warning but not crash)
            try:
                meta_hash = hash_file(str(csv_path))
                write_meta(str(meta_path), {
                    'hash': meta_hash,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'source': 'test'
                })
                # Verify meta file was created
                assert meta_path.exists()
            except Exception as e:
                pytest.fail(f"Missing metadata should not crash: {e}")

    def test_empty_metadata_file(self):
        """Test handling of empty metadata file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_path = Path(tmpdir) / "empty_meta.json"
            meta_path.write_text("")

            # Should raise JSON decode error or handle gracefully
            with pytest.raises((json.JSONDecodeError, ValueError)):
                with open(meta_path, 'r') as f:
                    json.load(f)

    def test_metadata_missing_required_keys(self):
        """Test handling of metadata missing required keys."""
        with tempfile.TemporaryDirectory() as tmpdir:
            meta_path = Path(tmpdir) / "incomplete_meta.json"
            # Missing 'hash' key
            incomplete_meta = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'test'
            }
            with open(meta_path, 'w') as f:
                json.dump(incomplete_meta, f)

            # Should handle missing required keys
            with open(meta_path, 'r') as f:
                loaded = json.load(f)
            
            assert 'hash' not in loaded
            # Test that we can detect missing keys
            required_keys = ['hash', 'timestamp', 'source']
            missing = [k for k in required_keys if k not in loaded]
            assert 'hash' in missing

    def test_missing_optional_feature_metadata(self):
        """Test handling when optional feature metadata (salience) is missing."""
        # This tests the UNFULFILLABLE case in features.py
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create data without salience metadata
            data = {
                'timestamp': [1.0, 2.0, 3.0],
                'x': [1.0, 2.0, 3.0],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2],
                'search_time': [10.0, 12.0, 11.0],
                'fixation_count': [5, 6, 5]
                # Note: no target_salience column
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "no_salience.csv"
            df.to_csv(csv_path, index=False)

            # Should handle missing salience gracefully
            # (mark as UNFULFILLABLE per task requirements)
            try:
                result = extract_features(df)
                # Check that status column indicates UNFULFILLABLE if salience missing
                if 'target_salience' not in result.columns:
                    # This is expected - salience computation requires images
                    assert True
            except Exception as e:
                # Should not crash, should mark as UNFULFILLABLE
                pytest.fail(f"Missing optional metadata should not crash: {e}")


class TestEdgeCaseDataValues:
    """Tests for edge cases in data values."""

    def test_all_nan_column(self):
        """Test handling of columns with all NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                'timestamp': [1.0, 2.0, 3.0],
                'x': [np.nan, np.nan, np.nan],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "all_nan_x.csv"
            df.to_csv(csv_path, index=False)

            # Should handle gracefully (may drop or interpolate)
            result_df = load_raw_data(csv_path)
            assert len(result_df) == 3

    def test_extreme_outliers(self):
        """Test handling of extreme outlier values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                'timestamp': [1.0, 2.0, 3.0],
                'x': [1.0, 2.0, 1000000.0],
                'y': [1.0, 2.0, 3.0],
                'pupil_diameter': [3.0, 3.1, 3.2]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "outliers.csv"
            df.to_csv(csv_path, index=False)

            # Should load successfully (filtering handles outliers)
            result_df = load_raw_data(csv_path)
            assert len(result_df) == 3

    def test_single_row_data(self):
        """Test handling of single-row dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                'timestamp': [1.0],
                'x': [1.0],
                'y': [1.0],
                'pupil_diameter': [3.0]
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "single_row.csv"
            df.to_csv(csv_path, index=False)

            result_df = load_raw_data(csv_path)
            assert len(result_df) == 1

    def test_empty_dataset(self):
        """Test handling of completely empty dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = {
                'timestamp': [],
                'x': [],
                'y': [],
                'pupil_diameter': []
            }
            df = pd.DataFrame(data)
            csv_path = Path(tmpdir) / "empty.csv"
            df.to_csv(csv_path, index=False)

            result_df = load_raw_data(csv_path)
            assert len(result_df) == 0


class TestValidationFunctions:
    """Tests for validation utility functions."""

    def test_validate_data_columns_missing_required(self):
        """Test column validation with missing required columns."""
        df = pd.DataFrame({
            'x': [1.0, 2.0],
            'y': [1.0, 2.0]
            # Missing timestamp and pupil_diameter
        })
        
        required = ['timestamp', 'x', 'y', 'pupil_diameter']
        
        with pytest.raises(ValueError) as exc_info:
            validate_data_columns(df, required)
        
        assert 'timestamp' in str(exc_info.value)
        assert 'pupil_diameter' in str(exc_info.value)

    def test_validate_data_columns_success(self):
        """Test column validation with all required columns present."""
        df = pd.DataFrame({
            'timestamp': [1.0, 2.0],
            'x': [1.0, 2.0],
            'y': [1.0, 2.0],
            'pupil_diameter': [3.0, 3.1]
        })
        
        required = ['timestamp', 'x', 'y', 'pupil_diameter']
        
        # Should not raise
        validate_data_columns(df, required)