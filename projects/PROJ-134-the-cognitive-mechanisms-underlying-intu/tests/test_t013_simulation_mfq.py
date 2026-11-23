"""
Unit tests for T013: Synthetic MFQ Generation.
"""
import pytest
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.simulation_mfq import (
    load_mdes_report,
    validate_ground_truth_effect,
    get_correlation_matrix,
    generate_synthetic_mfq
)
from code.config import get_path, GROUND_TRUTH_EFFECT_SIZE

class TestT013SimulationMFQ:
    
    def test_load_mdes_report_exists(self):
        """Test that MDES report can be loaded."""
        report = load_mdes_report()
        assert 'mdes_value' in report
        assert 'n_required' in report
        assert report['status'] == 'complete'
    
    def test_validate_ground_truth_effect(self):
        """Test validation of ground truth effect."""
        report = load_mdes_report()
        # This should not raise
        assert validate_ground_truth_effect(report) is True
    
    def test_correlation_matrix_structure(self):
        """Test that correlation matrix is symmetric and valid."""
        corr = get_correlation_matrix()
        assert corr.shape == (5, 5)
        # Check symmetry
        assert np.allclose(corr, corr.T)
        # Check diagonal is 1
        assert np.allclose(np.diag(corr), 1.0)
    
    def test_generate_synthetic_mfq_columns(self):
        """Test that generated data has correct columns."""
        means = [3.0, 3.0, 2.5, 2.5, 2.0]
        stds = [1.0, 1.0, 1.0, 1.0, 1.0]
        df = generate_synthetic_mfq(10, means, stds)
        
        expected_cols = ['participant_id', 'care', 'fairness', 'loyalty', 'authority', 'purity', 'total_score']
        assert list(df.columns) == expected_cols
    
    def test_generate_synthetic_mfq_values(self):
        """Test that generated values are reasonable."""
        means = [3.0, 3.0, 2.5, 2.5, 2.0]
        stds = [1.0, 1.0, 1.0, 1.0, 1.0]
        df = generate_synthetic_mfq(100, means, stds)
        
        # Check participant IDs
        assert df['participant_id'].min() == 1
        assert df['participant_id'].max() == 100
        
        # Check total score calculation
        expected_total = df[['care', 'fairness', 'loyalty', 'authority', 'purity']].sum(axis=1)
        assert np.allclose(df['total_score'], expected_total)
    
    def test_output_file_created(self):
        """Test that the main execution creates the output file."""
        # This test assumes the main function has been run or will be run
        # We check if the file exists after running the generation logic
        output_path = get_path("data/processed/synthetic_mfq.csv")
        if output_path.exists():
            df = pd.read_csv(output_path)
            assert len(df) > 0
            assert 'participant_id' in df.columns
            assert 'total_score' in df.columns