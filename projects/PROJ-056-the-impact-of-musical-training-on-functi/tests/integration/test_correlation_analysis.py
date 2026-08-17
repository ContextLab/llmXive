"""
Integration test for correlation analysis pipeline (User Story 3)
"""
import os
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.correlation import process_correlation_analysis
from data.synthetic_generator import generate_synthetic_dataset


class TestCorrelationAnalysisIntegration:
    """Integration tests for full correlation analysis pipeline"""

    @pytest.fixture
    def synthetic_data_setup(self, tmp_path):
        """Set up synthetic data for testing"""
        # Generate synthetic dataset
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True)
        
        processed_dir = data_dir / "processed"
        processed_dir.mkdir()
        
        # Generate synthetic subjects and connectivity
        n_subjects = 20
        subjects_df, connectivity_matrices = generate_synthetic_dataset(
            n_subjects=n_subjects,
            n_rois=5,
            include_connectivity=True
        )
        
        # Ensure some subjects are musicians
        subjects_df.loc[subjects_df['years_of_training'] < 1.0, 'years_of_training'] = np.random.uniform(1.0, 5.0, 
            size=sum(subjects_df['years_of_training'] < 1.0))
        
        # Save subjects
        subjects_file = processed_dir / "subjects_cleaned.csv"
        subjects_df.to_csv(subjects_file, index=False)
        
        # Save connectivity matrices
        conn_dir = processed_dir / "connectivity_matrices"
        conn_dir.mkdir()
        
        for i, (_, row) in enumerate(subjects_df.iterrows()):
            subject_id = row['subject_id']
            matrix = connectivity_matrices[i]
            np.save(conn_dir / f"{subject_id}_connectivity.npy", matrix)
        
        return {
            'subjects_file': str(subjects_file),
            'connectivity_dir': str(conn_dir),
            'output_file': str(processed_dir / "correlation_results.csv"),
            'tmp_path': tmp_path
        }

    def test_full_correlation_pipeline(self, synthetic_data_setup):
        """Test full correlation analysis pipeline"""
        result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=synthetic_data_setup['output_file'],
            method='pearson'
        )
        
        # Check output file exists
        assert os.path.exists(synthetic_data_setup['output_file'])
        
        # Check result DataFrame
        assert len(result) > 0
        assert 'connection_id' in result.columns
        assert 'r_value' in result.columns
        assert 'p_value' in result.columns
        assert 'ci_lower' in result.columns
        assert 'ci_upper' in result.columns
        assert 'effect_size' in result.columns
        
        # Check that we have connectivity results
        assert result['connection_id'].iloc[0].startswith('ROI')
        
        # Check that confidence intervals are reasonable
        assert (result['ci_lower'] < result['r_value']).all()
        assert (result['r_value'] < result['ci_upper']).all()

    def test_spearman_method(self, synthetic_data_setup):
        """Test Spearman correlation method"""
        output_file = synthetic_data_setup['tmp_path'] / "data/processed/correlation_spearman.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=str(output_file),
            method='spearman'
        )
        
        assert os.path.exists(str(output_file))
        assert len(result) > 0
        assert 'r_value' in result.columns

    def test_output_format(self, synthetic_data_setup):
        """Test that output file has correct format"""
        result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=synthetic_data_setup['output_file'],
            method='pearson'
        )
        
        # Load and verify CSV
        df = pd.read_csv(synthetic_data_setup['output_file'])
        
        required_columns = [
            'connection_id', 'r_value', 'p_value', 'effect_size', 
            'ci_lower', 'ci_upper'
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check data types
        assert df['r_value'].dtype in [np.float64, np.float32]
        assert df['p_value'].dtype in [np.float64, np.float32]
        
        # Check for NaN values (should be minimal)
        assert df['r_value'].isna().sum() < len(df) * 0.1  # Less than 10% NaN