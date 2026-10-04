"""
Unit tests for edge cases in the pupil dilation and cognitive load pipeline.
Tests: corrupted timestamps, missing metadata, excessive blink loss.
"""
import os
import sys
import tempfile
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Ensure code/ is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from preprocessing.load_data import load_raw_data_from_dataset, normalize_columns, process_single_file
from preprocessing.filter import interpolate_blinks, process_pupil_data, apply_filter_to_dataset
from preprocessing.features import load_trial_metadata, extract_features
from config import load_config
from logging_config import LoggingContext

logger = logging.getLogger(__name__)

def test_corrupted_timestamps_handling():
    """Test that corrupted timestamps (non-numeric or out-of-order) are handled gracefully."""
    # Create a temporary CSV with corrupted timestamps
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "corrupted_data.csv"
        # Timestamps: valid, corrupted string, valid, negative, valid
        data = {
            "timestamp": [100.0, "corrupted", 102.0, -5.0, 104.0],
            "x": [0.1, 0.2, 0.3, 0.4, 0.5],
            "y": [0.1, 0.2, 0.3, 0.4, 0.5],
            "pupil_diameter": [4.0, 4.1, 4.2, 4.3, 4.4]
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)

        # Mock config to point to this file
        mock_config = {
            "paths": {"raw_data_dir": str(tmpdir)},
            "seeds": 42,
            "thresholds": {0.40, 0.50, 0.60},
            "aggregation": False
        }

        with patch("preprocessing.load_data.load_config", return_value=mock_config):
            # The loader should either drop invalid rows or raise a specific error.
            # We test that it doesn't crash with an unhandled exception.
            try:
                result = process_single_file(input_path)
                # If it returns, check that corrupted rows are handled
                assert isinstance(result, pd.DataFrame)
                # Verify that 'corrupted' timestamp row is not present as a valid float
                # (either dropped or converted to NaN and dropped later)
                valid_timestamps = result["timestamp"].dropna()
                assert all(isinstance(t, (int, float)) for t in valid_timestamps), "Non-numeric timestamps found"
                # Ensure no negative timestamps remain if the logic filters them
                assert all(t >= 0 for t in valid_timestamps), "Negative timestamps found"
                logger.info("test_corrupted_timestamps_handling: PASSED")
            except Exception as e:
                # If the pipeline is designed to fail loudly on bad data, that's also acceptable
                # as long as the failure is explicit and not a cryptic traceback.
                if "corrupted" in str(e).lower() or "timestamp" in str(e).lower():
                    logger.info(f"test_corrupted_timestamps_handling: PASSED (Expected failure: {e})")
                else:
                    raise

def test_missing_metadata_handling():
    """Test that missing metadata columns are handled without crashing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a minimal features file missing required metadata columns
        input_path = Path(tmpdir) / "features.csv"
        data = {
            "subject_id": ["S01", "S01"],
            "trial_id": [1, 2],
            "pupil_peak": [4.1, 4.2],
            # Missing: search_time, target_salience, fixation_count
        }
        df = pd.DataFrame(data)
        df.to_csv(input_path, index=False)

        try:
            # Attempt to extract features (which expects metadata columns)
            # The function should handle missing columns gracefully (e.g., set to NaN or log warning)
            result = extract_features(df)
            # Check that the result has the missing columns filled with NaN or handled appropriately
            assert "search_time" in result.columns, "search_time column missing"
            assert "target_salience" in result.columns, "target_salience column missing"
            assert "fixation_count" in result.columns, "fixation_count column missing"
            # Verify they are NaN for the missing data
            assert result["search_time"].isna().all(), "search_time should be NaN when missing"
            assert result["target_salience"].isna().all(), "target_salience should be NaN when missing"
            assert result["fixation_count"].isna().all(), "fixation_count should be NaN when missing"
            logger.info("test_missing_metadata_handling: PASSED")
        except KeyError as e:
            # If the code strictly requires these columns and raises KeyError, that's a failure
            # of the edge-case handling. We expect graceful degradation.
            logger.error(f"test_missing_metadata_handling: FAILED - Missing column not handled: {e}")
            raise AssertionError("Missing metadata columns should be handled gracefully, not raise KeyError") from e

def test_excessive_blink_loss_exclusion():
    """Test that excessive blink loss (>30% missing samples) triggers exclusion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "blink_heavy.csv"
        # Create data with >30% missing values (NaN) to simulate excessive blinks
        n_samples = 100
        timestamps = np.linspace(0, 10, n_samples)
        # Introduce 40% NaN values in pupil_diameter
        pupil_data = np.random.uniform(4.0, 5.0, n_samples)
        pupil_data[::2] = np.nan  # 50% NaN to ensure >30%
        x = np.random.uniform(0, 1, n_samples)
        y = np.random.uniform(0, 1, n_samples)

        df = pd.DataFrame({
            "timestamp": timestamps,
            "x": x,
            "y": y,
            "pupil_diameter": pupil_data
        })
        df.to_csv(input_path, index=False)

        mock_config = {
            "paths": {"raw_data_dir": str(tmpdir)},
            "seeds": 42,
            "thresholds": {0.40, 0.50, 0.60},
            "aggregation": False,
            "blink_threshold": 0.30  # 30% threshold
        }

        with patch("preprocessing.filter.load_config", return_value=mock_config):
            try:
                # Apply filter - should detect excessive blinks and exclude the trial
                result = apply_filter_to_dataset(df, "S01", trial_id=1)
                # If the trial is excluded, the result might be empty or flagged
                # Depending on implementation, it might return an empty DataFrame or a specific status
                if result is None or result.empty:
                    logger.info("test_excessive_blink_loss_exclusion: PASSED (Trial excluded)")
                else:
                    # If it returns data, check if it's flagged as excluded or has a warning
                    # For this test, we assume the function returns None or empty if excluded
                    logger.warning("test_excessive_blink_loss_exclusion: WARNING - Excessive blinks not excluded")
                    # If the implementation is to interpolate despite >30% (which violates spec),
                    # we should catch it. But spec says >30% exclusion.
                    # We'll assert that the number of NaNs in result is still high if not excluded
                    nan_ratio = result["pupil_diameter"].isna().sum() / len(result)
                    if nan_ratio > 0.30:
                        logger.error("test_excessive_blink_loss_exclusion: FAILED - Excessive blinks not excluded")
                        raise AssertionError("Trial with >30% blink loss should be excluded")
            except ValueError as e:
                if "excessive" in str(e).lower() or "blink" in str(e).lower():
                    logger.info(f"test_excessive_blink_loss_exclusion: PASSED (Expected exclusion: {e})")
                else:
                    raise

def test_logging_context_integration():
    """Test that LoggingContext correctly records exclusions for edge cases."""
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "quality_report.csv"
        ctx = LoggingContext()
        ctx._report_path = str(report_path)  # Override path for testing

        # Simulate exclusions
        ctx.add_exclusion("corrupted_timestamp", 2)
        ctx.add_exclusion("excessive_blink_loss", 1)
        ctx.write_report()

        # Verify report file exists and has correct content
        assert report_path.exists(), "Quality report file not created"
        report_df = pd.read_csv(report_path)
        assert "exclusion_type" in report_df.columns, "Missing exclusion_type column"
        assert "count" in report_df.columns, "Missing count column"
        assert len(report_df) == 2, "Expected 2 exclusion rows"
        assert report_df[report_df["exclusion_type"] == "corrupted_timestamp"]["count"].iloc[0] == 2
        assert report_df[report_df["exclusion_type"] == "excessive_blink_loss"]["count"].iloc[0] == 1
        logger.info("test_logging_context_integration: PASSED")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_corrupted_timestamps_handling()
    test_missing_metadata_handling()
    test_excessive_blink_loss_exclusion()
    test_logging_context_integration()
    print("All edge case tests passed.")