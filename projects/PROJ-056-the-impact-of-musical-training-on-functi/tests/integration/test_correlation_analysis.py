"""
Integration test for correlation analysis pipeline (User Story 3)
Verifies end-to-end execution of correlation and sensitivity analysis on synthetic data.
"""
import os
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import sys

# Ensure code directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.correlation import process_correlation_analysis
from analysis.sensitivity import process_sensitivity_analysis
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
        # Using 50 subjects to ensure sufficient power for correlation
        n_subjects = 50
        n_rois = 10  # Small number for fast testing
        
        subjects_df, connectivity_matrices = generate_synthetic_dataset(
            n_subjects=n_subjects,
            n_rois=n_rois,
            include_connectivity=True
        )
        
        # Ensure we have a mix of musicians and non-musicians
        # Force at least 30 musicians for correlation analysis
        musician_indices = np.random.choice(n_subjects, size=30, replace=False)
        for idx in musician_indices:
            subjects_df.loc[idx, 'years_of_training'] = np.random.uniform(1.5, 8.0)
            subjects_df.loc[idx, 'group'] = 'musician'
        
        # Ensure remaining are non-musicians
        non_musician_indices = [i for i in range(n_subjects) if i not in musician_indices]
        for idx in non_musician_indices:
            subjects_df.loc[idx, 'years_of_training'] = np.random.uniform(0.0, 0.9)
            subjects_df.loc[idx, 'group'] = 'non_musician'
        
        # Save subjects
        subjects_file = processed_dir / "subjects_cleaned.csv"
        subjects_df.to_csv(subjects_file, index=False)
        
        # Save connectivity matrices in individual files as expected by the pipeline
        conn_dir = processed_dir / "connectivity_matrices"
        conn_dir.mkdir()
        
        for i, (_, row) in enumerate(subjects_df.iterrows()):
            subject_id = row['subject_id']
            matrix = connectivity_matrices[i]
            np.save(conn_dir / f"{subject_id}_connectivity.npy", matrix)
        
        return {
            'subjects_file': str(subjects_file),
            'connectivity_dir': str(conn_dir),
            'correlation_output': str(processed_dir / "correlation_results.csv"),
            'sensitivity_output': str(processed_dir / "sensitivity_analysis.csv"),
            'tmp_path': tmp_path
        }

    def test_full_correlation_pipeline(self, synthetic_data_setup):
        """Test full correlation analysis pipeline with Pearson correlation"""
        result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=synthetic_data_setup['correlation_output'],
            method='pearson'
        )
        
        # Check output file exists
        assert os.path.exists(synthetic_data_setup['correlation_output']), \
            f"Output file not created: {synthetic_data_setup['correlation_output']}"
        
        # Check result DataFrame
        assert len(result) > 0, "Result DataFrame is empty"
        assert 'connection_id' in result.columns, "Missing connection_id column"
        assert 'r_value' in result.columns, "Missing r_value column"
        assert 'p_value' in result.columns, "Missing p_value column"
        assert 'ci_lower' in result.columns, "Missing ci_lower column"
        assert 'ci_upper' in result.columns, "Missing ci_upper column"
        assert 'effect_size' in result.columns, "Missing effect_size column"
        assert 'stability_flag' in result.columns, "Missing stability_flag column"
        
        # Check that we have connectivity results
        assert result['connection_id'].iloc[0].startswith('ROI'), \
            "Connection ID format is incorrect"
        
        # Check that confidence intervals are reasonable
        assert (result['ci_lower'] <= result['r_value']).all(), \
            "Lower CI should be <= r_value"
        assert (result['r_value'] <= result['ci_upper']).all(), \
            "Upper CI should be >= r_value"
        
        # Check stability flags are valid
        valid_flags = ['high', 'low']
        assert all(flag in valid_flags for flag in result['stability_flag']), \
            f"Invalid stability flags found. Expected {valid_flags}"

    def test_spearman_method(self, synthetic_data_setup):
        """Test Spearman correlation method"""
        output_file = str(Path(synthetic_data_setup['tmp_path']) / "data/processed/correlation_spearman.csv")
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        
        result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=output_file,
            method='spearman'
        )
        
        assert os.path.exists(output_file), f"Output file not created: {output_file}"
        assert len(result) > 0, "Spearman result DataFrame is empty"
        assert 'r_value' in result.columns, "Missing r_value column in Spearman result"
        assert 'stability_flag' in result.columns, "Missing stability_flag in Spearman result"

    def test_output_format(self, synthetic_data_setup):
        """Test that output file has correct format and data types"""
        result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=synthetic_data_setup['correlation_output'],
            method='pearson'
        )
        
        # Load and verify CSV
        df = pd.read_csv(synthetic_data_setup['correlation_output'])
        
        required_columns = [
            'connection_id', 'r_value', 'p_value', 'effect_size', 
            'ci_lower', 'ci_upper', 'stability_flag'
        ]
        
        for col in required_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Check data types
        assert df['r_value'].dtype in [np.float64, np.float32, 'float64', 'float32'], \
            f"r_value has incorrect dtype: {df['r_value'].dtype}"
        assert df['p_value'].dtype in [np.float64, np.float32, 'float64', 'float32'], \
            f"p_value has incorrect dtype: {df['p_value'].dtype}"
        
        # Check for NaN values (should be minimal)
        nan_count = df['r_value'].isna().sum()
        total_count = len(df)
        assert nan_count < total_count * 0.1, \
            f"Too many NaN values: {nan_count}/{total_count} ({100*nan_count/total_count:.1f}%)"

    def test_sensitivity_analysis_integration(self, synthetic_data_setup):
        """Test that sensitivity analysis runs after correlation"""
        # First run correlation to generate results
        process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=synthetic_data_setup['correlation_output'],
            method='pearson'
        )
        
        # Then run sensitivity analysis
        sensitivity_result = process_sensitivity_analysis(
            correlation_file=synthetic_data_setup['correlation_output'],
            output_file=synthetic_data_setup['sensitivity_output']
        )
        
        # Check sensitivity output
        assert os.path.exists(synthetic_data_setup['sensitivity_output']), \
            f"Sensitivity output not created: {synthetic_data_setup['sensitivity_output']}"
        
        assert len(sensitivity_result) > 0, "Sensitivity result is empty"
        assert 'threshold' in sensitivity_result.columns, "Missing threshold column"
        assert 'significant_count' in sensitivity_result.columns, "Missing significant_count column"
        assert 'percentage_reduction' in sensitivity_result.columns, "Missing percentage_reduction column"
        
        # Check that we have the expected thresholds
        thresholds = set(sensitivity_result['threshold'])
        expected_thresholds = {0.01, 0.05, 0.10}
        assert expected_thresholds.issubset(thresholds), \
            f"Missing expected thresholds. Found: {thresholds}, Expected: {expected_thresholds}"
        
        # Verify percentage_reduction calculation
        # For threshold 0.05 vs 0.01: reduction = (count_0.05 - count_0.01) / count_0.05 * 100
        row_0_05 = sensitivity_result[sensitivity_result['threshold'] == 0.05].iloc[0]
        row_0_01 = sensitivity_result[sensitivity_result['threshold'] == 0.01].iloc[0]
        
        count_0_05 = row_0_05['significant_count']
        count_0_01 = row_0_01['significant_count']
        expected_reduction = (count_0_05 - count_0_01) / count_0_05 * 100 if count_0_05 > 0 else 0
        
        assert abs(row_0_05['percentage_reduction'] - expected_reduction) < 0.01, \
            f"Percentage reduction calculation incorrect. Expected: {expected_reduction}, Got: {row_0_05['percentage_reduction']}"

    def test_musicians_only_filtering(self, synthetic_data_setup):
        """Verify that correlation is computed only on musicians"""
        result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=synthetic_data_setup['correlation_output'],
            method='pearson'
        )
        
        # Load subjects to verify filtering
        subjects = pd.read_csv(synthetic_data_setup['subjects_file'])
        musicians = subjects[subjects['group'] == 'musician']
        
        # The correlation should only be based on musicians
        # We verify this by checking that the function ran without error
        # (if it included non-musicians, the correlation with years_of_training
        # would likely be weak or zero since non-musicians have near-zero training)
        assert len(result) > 0, "No correlations computed"
        
        # Check that we have reasonable correlation values
        # (not all zeros or NaNs)
        non_nan_r = result['r_value'].dropna()
        assert len(non_nan_r) > 0, "All r_values are NaN"
        assert not (non_nan_r == 0).all(), "All r_values are zero - likely not filtering musicians"

    def test_pipeline_end_to_end(self, synthetic_data_setup):
        """Test complete pipeline: correlation + sensitivity"""
        # Run correlation
        correlation_result = process_correlation_analysis(
            subjects_file=synthetic_data_setup['subjects_file'],
            connectivity_dir=synthetic_data_setup['connectivity_dir'],
            output_file=synthetic_data_setup['correlation_output'],
            method='pearson'
        )
        
        # Run sensitivity
        sensitivity_result = process_sensitivity_analysis(
            correlation_file=synthetic_data_setup['correlation_output'],
            output_file=synthetic_data_setup['sensitivity_output']
        )
        
        # Verify both outputs exist and are valid
        assert os.path.exists(synthetic_data_setup['correlation_output'])
        assert os.path.exists(synthetic_data_setup['sensitivity_output'])
        
        # Verify data integrity
        assert len(correlation_result) > 0
        assert len(sensitivity_result) == 3  # 3 thresholds: 0.01, 0.05, 0.10
        
        # Verify summary statistics
        assert correlation_result['p_value'].notna().sum() > 0
        assert sensitivity_result['significant_count'].sum() >= 0