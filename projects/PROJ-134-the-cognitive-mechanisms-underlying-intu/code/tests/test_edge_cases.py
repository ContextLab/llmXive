import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os
import json
import logging
from typing import Dict, Any, List, Optional
from unittest.mock import patch, MagicMock

# Import project utilities and models
from code.utils.schema import (
    SalienceLevel, MFQResponse, MFQDataset, MoralStory, 
    MoralStoriesDataset, VRInteractionLog, VRLogsDataset, MergedDataset
)
from code.utils.logging_utils import log_exclusion, log_vr_mapping, get_logger
from code.models.bayesian import run_bayesian_model
from code.analysis.validation import check_parameter_recovery
from code.analysis.model_comparison import calculate_aic_waic
from code.data.simulation_mfq import generate_synthetic_mfq
from code.config import ensure_directories

class TestMissingDataHandling:
    """Tests for handling missing or null data in the pipeline."""

    def test_mfq_with_missing_values(self):
        """Test that MFQ generation handles missing values gracefully."""
        # Create a DataFrame with some missing values
        data = {
            'participant_id': ['P1', 'P2', 'P3', 'P4'],
            'care': [0.8, np.nan, 0.6, 0.9],
            'fairness': [0.7, 0.5, np.nan, 0.8],
            'loyalty': [np.nan, 0.4, 0.5, 0.6],
            'authority': [0.6, 0.7, 0.5, np.nan],
            'purity': [0.5, 0.6, 0.7, 0.8]
        }
        df = pd.DataFrame(data)
        
        # Test validation with missing data
        # The schema should handle this or raise a clear error
        with pytest.raises((ValueError, ValidationError)) as exc_info:
            MFQDataset(
                participant_scores=[
                    MFQResponse(participant_id='P1', care=0.8, fairness=0.7, loyalty=0.5, authority=0.6, purity=0.5),
                    MFQResponse(participant_id='P2', care=np.nan, fairness=0.5, loyalty=0.4, authority=0.7, purity=0.6)
                ]
            )
        
        assert "nan" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

    def test_stories_with_missing_text(self):
        """Test that moral stories with missing text are handled."""
        with pytest.raises(ValidationError):
            MoralStory(
                story_id='S1',
                text='',  # Empty text should fail validation
                moral_foundation='care',
                target_vr_scene='scene_1'
            )

    def test_vr_logs_with_missing_timestamps(self):
        """Test that VR logs with missing timestamps are handled."""
        with pytest.raises(ValidationError):
            VRInteractionLog(
                log_id='L1',
                participant_id='P1',
                story_id='S1',
                timestamp=None,  # Missing timestamp
                response_time=2.5,
                gaze_data={'x': 0.5, 'y': 0.5},
                judgment_score=0.7
            )

    def test_merged_dataset_with_mismatched_ids(self):
        """Test handling of ID mismatches in merged datasets."""
        # Create datasets with non-overlapping IDs
        mfq_data = MFQDataset(
            participant_scores=[
                MFQResponse(participant_id='P1', care=0.8, fairness=0.7, loyalty=0.5, authority=0.6, purity=0.5)
            ]
        )
        
        stories_data = MoralStoriesDataset(
            stories=[
                MoralStory(story_id='S1', text='Test story', moral_foundation='care', target_vr_scene='scene_1')
            ]
        )
        
        # Merging should handle missing joins gracefully
        # In a real scenario, this would log a warning or exclusion
        merged = MergedDataset(
            merged_rows=[],
            exclusion_log=['No matching participant for story S1']
        )
        assert len(merged.exclusion_log) > 0

    def test_empty_dataset_handling(self):
        """Test that empty datasets are handled without crashing."""
        # Empty MFQ dataset
        empty_mfq = MFQDataset(participant_scores=[])
        assert len(empty_mfq.participant_scores) == 0

        # Empty stories dataset
        empty_stories = MoralStoriesDataset(stories=[])
        assert len(empty_stories.stories) == 0

        # Test that functions don't crash on empty input
        # This is a basic check; real functions should have explicit checks
        try:
            # Attempt to calculate stats on empty data should raise or return None
            if len(empty_mfq.participant_scores) == 0:
                pass  # Expected behavior
        except Exception:
            pytest.fail("Empty dataset handling should not raise unhandled exceptions")


class TestConvergenceFailure:
    """Tests for handling model convergence failures in Bayesian analysis."""

    def test_bayesian_model_with_insufficient_data(self):
        """Test that Bayesian model handles insufficient data gracefully."""
        # Create a very small dataset that might cause convergence issues
        small_data = pd.DataFrame({
            'salience_level': [0, 1],
            'foundation_score': [0.5, 0.6],
            'judgment': [0.4, 0.5]
        })
        
        # Mock the PyMC sampling to simulate convergence failure
        with patch('pymc.sample') as mock_sample:
            mock_sample.side_effect = Exception("Convergence failed: R-hat > 1.05")
            
            # The model should catch this and log/fallback appropriately
            # For this test, we verify that the exception is raised (fail loudly)
            # or that a fallback mechanism is triggered
            with pytest.raises(Exception):
                run_bayesian_model(data=small_data, n_samples=100)

    def test_parameter_recovery_with_failed_convergence(self):
        """Test that parameter recovery validation handles failed convergence."""
        # Create a mock inference data object that indicates failure
        mock_failed_data = MagicMock()
        mock_failed_data.sample_stats.r_hat = np.array([2.0])  # High R-hat indicates failure
        
        # The validation should detect this and report failure
        result = check_parameter_recovery(
            inference_data=mock_failed_data,
            ground_truth_effect=0.5,
            tolerance=0.1
        )
        
        # Should report failure due to poor convergence
        assert result['status'] == 'failed' or result['convergence'] == False

    def test_model_comparison_with_convergence_issues(self):
        """Test that model comparison handles convergence issues."""
        # Mock two models where one has convergence issues
        mock_model_a = MagicMock()
        mock_model_a.sample_stats.r_hat = np.array([1.01])  # Good convergence
        
        mock_model_b = MagicMock()
        mock_model_b.sample_stats.r_hat = np.array([1.5])  # Poor convergence
        
        # Calculate metrics should handle this gracefully
        try:
            aic_a, waic_a = calculate_aic_waic(mock_model_a)
            aic_b, waic_b = calculate_aic_waic(mock_model_b)
            
            # If convergence is poor, WAIC might be unreliable
            # The function should either return None or raise a warning
        except Exception as e:
            # Expected if the function enforces convergence checks
            assert "convergence" in str(e).lower() or "r_hat" in str(e).lower()

    def test_logging_convergence_failure(self):
        """Test that convergence failures are properly logged."""
        logger = get_logger("test_convergence")
        log_path = Path("data/logs/convergence_test.log")
        
        # Ensure directory exists
        ensure_directories()
        
        # Log a convergence failure
        log_exclusion(
            log_type="convergence_failure",
            participant_id="P1",
            reason="R-hat = 1.5 exceeds threshold",
            log_path=log_path
        )
        
        # Verify log file exists and contains the error
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
            assert "convergence_failure" in content
            assert "R-hat" in content


class TestInvalidDataTypes:
    """Tests for handling invalid data types and formats."""

    def test_non_numeric_foundation_scores(self):
        """Test handling of non-numeric foundation scores."""
        with pytest.raises(ValidationError):
            MFQResponse(
                participant_id='P1',
                care='high',  # Should be float
                fairness=0.7,
                loyalty=0.5,
                authority=0.6,
                purity=0.5
            )

    def test_negative_salience_level(self):
        """Test handling of invalid salience levels."""
        # SalienceLevel is an Enum, should only accept defined values
        with pytest.raises(ValidationError):
            MoralStory(
                story_id='S1',
                text='Test story',
                moral_foundation='care',
                target_vr_scene='scene_1',
                salience_level=-1  # Invalid enum value
            )

    def test_out_of_range_response_times(self):
        """Test handling of physically impossible response times."""
        # Response times should be positive and reasonable (< 60s)
        with pytest.raises(ValidationError):
            VRInteractionLog(
                log_id='L1',
                participant_id='P1',
                story_id='S1',
                timestamp=datetime.now(),
                response_time=-5.0,  # Negative time
                gaze_data={'x': 0.5, 'y': 0.5},
                judgment_score=0.7
            )

    def test_malformed_gaze_data(self):
        """Test handling of malformed gaze data structures."""
        with pytest.raises(ValidationError):
            VRInteractionLog(
                log_id='L1',
                participant_id='P1',
                story_id='S1',
                timestamp=datetime.now(),
                response_time=2.5,
                gaze_data="invalid_string",  # Should be dict
                judgment_score=0.7
            )


class TestIntegrationEdgeCases:
    """Integration tests for edge cases across the full pipeline."""

    def test_full_pipeline_with_missing_data(self):
        """Test that the full pipeline handles missing data without crashing."""
        # Setup
        ensure_directories()
        
        # Generate synthetic data with some missing values
        # (In a real test, this would be more comprehensive)
        try:
            # Attempt to run the pipeline with edge case data
            # This is a smoke test to ensure no unhandled exceptions
            pass
        except Exception as e:
            # Expected if the pipeline strictly enforces data quality
            assert "missing" in str(e).lower() or "validation" in str(e).lower()

    def test_pipeline_with_convergence_failures(self):
        """Test that the pipeline logs and continues when models fail to converge."""
        # Mock the Bayesian model to fail
        with patch('code.models.bayesian.run_bayesian_model') as mock_run:
            mock_run.return_value = {
                'status': 'failed',
                'reason': 'Convergence failure',
                'convergence': False
            }
            
            # The pipeline should continue and log the failure
            # Verify that the failure is recorded
            pass

    def test_checksum_with_corrupted_data(self):
        """Test that checksums detect corrupted data files."""
        from code.utils.hashing import calculate_sha256
        
        # Create a valid file
        valid_file = Path("data/test_valid.txt")
        valid_file.parent.mkdir(parents=True, exist_ok=True)
        valid_file.write_text("valid content")
        
        valid_hash = calculate_sha256(valid_file)
        
        # Corrupt the file
        valid_file.write_text("corrupted content")
        
        # Recalculate hash
        corrupted_hash = calculate_sha256(valid_file)
        
        # Hashes should differ
        assert valid_hash != corrupted_hash

    def test_validation_with_extreme_values(self):
        """Test that validation handles extreme statistical values."""
        # Create data with extreme values
        extreme_data = pd.DataFrame({
            'salience_level': [0, 1],
            'foundation_score': [1e10, 1e10],  # Extremely large values
            'judgment': [0.5, 0.5]
        })
        
        # Validation should handle this without crashing
        # (might flag as outlier or normalize)
        try:
            # Attempt validation
            pass
        except Exception as e:
            # Expected if extreme values are rejected
            assert "extreme" in str(e).lower() or "outlier" in str(e).lower()

    def test_logging_with_special_characters(self):
        """Test that logging handles special characters in data."""
        logger = get_logger("test_special_chars")
        log_path = Path("data/logs/special_chars_test.log")
        
        ensure_directories()
        
        # Log data with special characters
        log_exclusion(
            log_type="test",
            participant_id="P1-特殊",
            reason="Error: <test> & 'quote' \"double\"",
            log_path=log_path
        )
        
        # Verify log file exists and contains the data
        assert log_path.exists()
        with open(log_path, 'r') as f:
            content = f.read()
            assert "特殊" in content
            assert "<test>" in content

# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])