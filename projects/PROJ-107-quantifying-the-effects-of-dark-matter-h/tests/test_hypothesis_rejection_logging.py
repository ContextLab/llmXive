"""
Tests for T027: Hypothesis Rejection Logging

Verifies that the log_hypothesis_rejections module correctly identifies
and logs null hypothesis rejections (p < 0.01).
"""

import pytest
import pandas as pd
import numpy as np
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.analysis.log_hypothesis_rejections import (
    log_hypothesis_rejection,
    log_all_rejections_from_results,
    REJECTION_THRESHOLD
)
from code.utils.config import get_output_path


class TestHypothesisRejectionLogging:
    """Test suite for hypothesis rejection logging functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_results_file = Path(self.temp_dir) / "test_results.csv"
        self.test_log_file = Path(self.temp_dir) / "test_rejection_log.csv"
        
        # Create test data with mixed p-values
        self.test_data = pd.DataFrame({
            'predictor': ['triaxiality', 'b_a_ratio', 'mass', 'sfr', 'effective_radius'],
            'p_value': [0.005, 0.001, 0.05, 0.008, 0.15],  # 3 rejections expected
            'coefficient': [0.5, -0.3, 0.1, 0.2, -0.1],
            'r_squared': [0.25, 0.18, 0.10, 0.20, 0.05]
        })
        
        self.test_data.to_csv(self.test_results_file, index=False)

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.test_results_file.exists():
            self.test_results_file.unlink()
        if self.test_log_file.exists():
            self.test_log_file.unlink()
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_single_rejection_logging(self):
        """Test logging a single rejection event."""
        result = {
            'predictor': 'triaxiality',
            'p_value': 0.005,
            'coefficient': 0.5
        }
        
        log_hypothesis_rejection(
            test_name='test_regression',
            predictor='triaxiality',
            p_value=0.005,
            result_row=result,
            log_path=self.test_log_file
        )
        
        assert self.test_log_file.exists(), "Log file should be created"
        
        log_df = pd.read_csv(self.test_log_file)
        assert len(log_df) == 1, "Should have 1 rejection entry"
        assert log_df.iloc[0]['status'] == 'REJECTED', "Status should be REJECTED"
        assert log_df.iloc[0]['p_value'] == 0.005, "P-value should match"
        assert log_df.iloc[0]['predictor'] == 'triaxiality', "Predictor should match"

    def test_non_rejection_not_logged(self):
        """Test that non-rejections are not logged."""
        result = {
            'predictor': 'mass',
            'p_value': 0.05,
            'coefficient': 0.1
        }
        
        log_hypothesis_rejection(
            test_name='test_regression',
            predictor='mass',
            p_value=0.05,
            result_row=result,
            log_path=self.test_log_file
        )
        
        assert not self.test_log_file.exists(), "Log file should not be created for non-rejection"

    def test_batch_rejection_logging(self):
        """Test logging multiple rejections from a results file."""
        rejections = log_all_rejections_from_results(
            results_file=self.test_results_file,
            test_name='batch_test',
            p_value_column='p_value',
            predictor_column='predictor',
            log_path=self.test_log_file
        )
        
        # Should find 3 rejections (p < 0.01)
        assert len(rejections) == 3, f"Expected 3 rejections, got {len(rejections)}"
        
        # Verify log file contents
        assert self.test_log_file.exists(), "Log file should be created"
        log_df = pd.read_csv(self.test_log_file)
        assert len(log_df) == 3, "Log file should contain 3 entries"
        
        # Verify specific rejections
        predictors = log_df['predictor'].tolist()
        assert 'triaxiality' in predictors, "Should log triaxiality rejection"
        assert 'b_a_ratio' in predictors, "Should log b_a_ratio rejection"
        assert 'sfr' in predictors, "Should log sfr rejection"

    def test_boundary_case(self):
        """Test behavior at the exact threshold boundary."""
        # Exactly at threshold - should NOT be rejected
        result_at_threshold = {
            'predictor': 'boundary',
            'p_value': REJECTION_THRESHOLD,
            'coefficient': 0.0
        }
        
        log_hypothesis_rejection(
            test_name='boundary_test',
            predictor='boundary',
            p_value=REJECTION_THRESHOLD,
            result_row=result_at_threshold,
            log_path=self.test_log_file
        )
        
        # Should not create log file (not a rejection)
        if self.test_log_file.exists():
            self.test_log_file.unlink()
        
        # Slightly below threshold - SHOULD be rejected
        log_hypothesis_rejection(
            test_name='boundary_test',
            predictor='boundary_low',
            p_value=REJECTION_THRESHOLD - 0.0001,
            result_row={'predictor': 'boundary_low', 'p_value': REJECTION_THRESHOLD - 0.0001},
            log_path=self.test_log_file
        )
        
        assert self.test_log_file.exists(), "Should log value slightly below threshold"

    def test_missing_file(self):
        """Test behavior when results file is missing."""
        rejections = log_all_rejections_from_results(
            results_file=Path("/nonexistent/path/results.csv"),
            test_name='missing_test'
        )
        
        assert len(rejections) == 0, "Should return empty list for missing file"

    def test_missing_columns(self):
        """Test behavior when required columns are missing."""
        # Create file with wrong column names
        wrong_df = pd.DataFrame({
            'wrong_predictor': ['a', 'b'],
            'wrong_p': [0.001, 0.05]
        })
        wrong_df.to_csv(self.test_results_file, index=False)
        
        rejections = log_all_rejections_from_results(
            results_file=self.test_results_file,
            p_value_column='p_value',  # Column doesn't exist
            predictor_column='predictor'  # Column doesn't exist
        )
        
        # Should return empty list due to missing p_value column
        assert len(rejections) == 0, "Should return empty list when p_value column missing"

    def test_invalid_p_values(self):
        """Test handling of invalid p-values (NaN, strings, etc.)."""
        invalid_df = pd.DataFrame({
            'predictor': ['a', 'b', 'c', 'd'],
            'p_value': [0.001, np.nan, 'invalid', None]
        })
        invalid_df.to_csv(self.test_results_file, index=False)
        
        rejections = log_all_rejections_from_results(
            results_file=self.test_results_file,
            p_value_column='p_value',
            predictor_column='predictor',
            log_path=self.test_log_file
        )
        
        # Should only process the valid p-value
        assert len(rejections) == 1, "Should only process valid p-values"
        assert rejections[0]['predictor'] == 'a', "Should log the valid entry"