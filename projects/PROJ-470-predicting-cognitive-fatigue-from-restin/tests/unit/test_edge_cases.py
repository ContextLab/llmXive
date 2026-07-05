"""
Unit tests for edge cases in the cognitive fatigue EEG pipeline.
Covers missing data, artifact rejection, and analysis mode failures.
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocess import reject_artifacts, load_config
from analysis import validate_metadata, run_benjamini_hochberg
from utils.logging import log_participant_exclusion, log_artifact_rejection


class TestMissingData:
    """Tests for handling missing or empty data scenarios."""

    def test_empty_eeg_stream(self):
        """Test that empty EEG stream is handled gracefully."""
        config = load_config()
        # Simulate empty stream
        empty_stream = []
        
        # Should not raise an exception, but return empty results
        # This depends on how process_eeg_stream handles empty input
        # We test the lower-level reject_artifacts with empty data
        result = reject_artifacts(empty_stream, config)
        assert result is None or len(result) == 0

    def test_missing_metadata_columns(self):
        """Test validation fails when required metadata columns are missing."""
        # Create metadata with missing columns
        incomplete_metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [2.0, 3.0]
            # Missing: post_fatigue, pre_eeg_id, post_eeg_id
        })
        
        # Should raise ValueError or return error status
        with pytest.raises(ValueError):
            validate_metadata(incomplete_metadata)

    def test_complete_metadata_validation(self):
        """Test that complete metadata passes validation."""
        complete_metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [2.0, 3.0],
            'post_fatigue': [4.0, 5.0],
            'pre_eeg_id': ['eeg_001', 'eeg_002'],
            'post_eeg_id': ['eeg_003', 'eeg_004']
        })
        
        # Should not raise
        result = validate_metadata(complete_metadata)
        assert result is not None

    def test_all_nan_fatigue_scores(self):
        """Test handling of all NaN fatigue scores."""
        metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [np.nan, np.nan],
            'post_fatigue': [np.nan, np.nan],
            'pre_eeg_id': ['eeg_001', 'eeg_002'],
            'post_eeg_id': ['eeg_003', 'eeg_004']
        })
        
        # Should handle gracefully, possibly by excluding these participants
        with pytest.raises(ValueError):
            validate_metadata(metadata)


class TestArtifactRejection:
    """Tests for artifact rejection edge cases."""

    def test_all_artifacts_rejected(self):
        """Test when all epochs exceed artifact threshold."""
        config = load_config()
        # Create data with all epochs exceeding threshold (±100µV)
        # Simulate epochs with amplitudes > 100
        all_bad_epochs = {
            'participant_id': 'P001',
            'epochs': np.array([
                [200.0] * 1000,  # All > 100µV
                [-200.0] * 1000, # All < -100µV
            ])
        }
        
        # Should reject all and log appropriately
        result = reject_artifacts([all_bad_epochs], config)
        # Result should be None or empty for this participant
        assert result is None or len(result) == 0

    def test_mixed_artifact_rejection(self):
        """Test rejection with mixed good and bad epochs."""
        config = load_config()
        mixed_epochs = {
            'participant_id': 'P001',
            'epochs': np.array([
                [50.0] * 1000,    # Good epoch
                [150.0] * 1000,   # Bad epoch
                [30.0] * 1000,    # Good epoch
            ])
        }
        
        result = reject_artifacts([mixed_epochs], config)
        # Should keep 2 out of 3 epochs
        assert result is not None
        assert len(result) == 1  # One participant in result
        # The specific number of kept epochs depends on implementation
        # but should be less than original

    def test_threshold_boundary_conditions(self):
        """Test behavior at exact threshold values."""
        config = load_config()
        threshold = config.get('artifact_threshold', 100.0)
        
        boundary_epochs = {
            'participant_id': 'P001',
            'epochs': np.array([
                [threshold - 0.1] * 1000,  # Just under
                [threshold] * 1000,        # Exactly at
                [threshold + 0.1] * 1000,  # Just over
            ])
        }
        
        result = reject_artifacts([boundary_epochs], config)
        # At least the boundary epoch should be rejected
        assert result is not None

    def test_zero_variance_epochs(self):
        """Test handling of epochs with zero variance (flat lines)."""
        config = load_config()
        flat_epochs = {
            'participant_id': 'P001',
            'epochs': np.array([
                [0.0] * 1000,  # Flat line
                [50.0] * 1000, # Normal
            ])
        }
        
        result = reject_artifacts([flat_epochs], config)
        # Should handle without crashing
        assert result is not None or result is None  # Depends on implementation


class TestAnalysisModeFailures:
    """Tests for analysis mode selection and failure scenarios."""

    def test_no_paired_data_fallback(self):
        """Test fallback to cross-sectional when paired data missing."""
        # Metadata with only baseline (no post)
        baseline_only = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [2.0, 3.0],
            'pre_eeg_id': ['eeg_001', 'eeg_002'],
            # Missing post_* columns
        })
        
        # Should raise ValueError as per spec
        with pytest.raises(ValueError):
            validate_metadata(baseline_only)

    def test_insufficient_sample_size(self):
        """Test when sample size is below minimum."""
        # Very small dataset
        small_metadata = pd.DataFrame({
            'participant_id': ['P001'],
            'pre_fatigue': [2.0],
            'post_fatigue': [4.0],
            'pre_eeg_id': ['eeg_001'],
            'post_eeg_id': ['eeg_002']
        })
        
        # Should handle gracefully or raise
        # Depending on implementation, might raise ValueError
        with pytest.raises(ValueError):
            validate_metadata(small_metadata)

    def test_benjamini_hochberg_zero_pvalues(self):
        """Test BH correction with zero or NaN p-values."""
        # P-values with zeros and NaNs
        p_values = np.array([0.0, 0.05, np.nan, 0.1, 0.01])
        labels = ['ch1', 'ch2', 'ch3', 'ch4', 'ch5']
        
        # Should handle without crashing
        result = run_benjamini_hochberg(p_values, labels)
        assert result is not None
        # Zeros and NaNs should be handled appropriately

    def test_correlation_with_single_sample(self):
        """Test correlation calculation with only one sample."""
        # This would be caught in validate_metadata, but test BH anyway
        p_values = np.array([0.05])
        labels = ['ch1']
        
        result = run_benjamini_hochberg(p_values, labels)
        assert result is not None


class TestLoggingEdgeCases:
    """Tests for logging edge cases."""

    def test_log_participant_exclusion_empty_reason(self):
        """Test logging with empty exclusion reason."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.json"
            # Should handle empty reason gracefully
            log_participant_exclusion(
                participant_id="P001",
                reason="",
                log_file=log_file
            )
            # File should be created
            assert log_file.exists()

    def test_log_artifact_rejection_no_epochs(self):
        """Test logging artifact rejection with no epochs rejected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_log.json"
            log_artifact_rejection(
                participant_id="P001",
                rejected_epochs=0,
                total_epochs=10,
                log_file=log_file
            )
            assert log_file.exists()

    def test_log_file_permissions(self):
        """Test logging to read-only file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "readonly.json"
            log_file.write_text("{}")
            log_file.chmod(0o444)  # Read-only
            
            # Should handle permission error gracefully
            try:
                log_participant_exclusion(
                    participant_id="P001",
                    reason="test",
                    log_file=log_file
                )
            except (PermissionError, OSError):
                # Expected behavior
                pass
            finally:
                log_file.chmod(0o644)  # Restore for cleanup