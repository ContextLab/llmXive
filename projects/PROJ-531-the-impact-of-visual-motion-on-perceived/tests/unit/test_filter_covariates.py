"""
Unit tests for T018: Covariate Filtering Logic.

Tests the validation logic that excludes trait/personality measures
from primary regression while allowing them as covariates.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json
import os

# Import the module under test
from code.preprocessing.filter_covariates import (
    is_trait_measure,
    filter_features_for_primary_regression,
    run_covariate_filtering
)

class TestIsTraitMeasure:
    """Tests for the is_trait_measure function."""
    
    def test_known_trait_measures(self):
        """Test that known trait measures are correctly identified."""
        traits = [
            'neuroticism', 'extraversion', 'openness', 
            'social_anxiety', 'empathy_score', 'age', 'gender',
            'post_task_rating', 'self_report_agency'
        ]
        for trait in traits:
            assert is_trait_measure(trait), f"Failed to identify {trait} as trait measure"
    
    def test_known_motion_features(self):
        """Test that motion features are NOT identified as traits."""
        motion_features = [
            'latency', 'smoothness', 'lead_time', 'jerk', 
            'velocity', 'acceleration', 'trajectory_deviation'
        ]
        for feature in motion_features:
            assert not is_trait_measure(feature), f"False positive: {feature} identified as trait"
    
    def test_case_insensitivity(self):
        """Test that detection is case-insensitive."""
        assert is_trait_measure('NEUROTICISM')
        assert is_trait_measure('Latency')
        assert not is_trait_measure('LATENCY')
    
    def test_compound_names(self):
        """Test compound names containing trait keywords."""
        assert is_trait_measure('big5_neuroticism_score')
        assert is_trait_measure('post_task_agency_rating')
        assert is_trait_measure('subjective_smoothness_score')

class TestFilterFeaturesForPrimaryRegression:
    """Tests for the feature filtering logic."""
    
    def test_separation_logic(self):
        """Test that features are correctly separated."""
        data = {
            'latency': [1, 2, 3],
            'smoothness': [4, 5, 6],
            'neuroticism': [7, 8, 9],
            'age': [10, 11, 12],
            'lead_time': [13, 14, 15],
            'agency_score': [16, 17, 18]
        }
        df = pd.DataFrame(data)
        
        primary, covariates = filter_features_for_primary_regression(df, target_col='agency_score')
        
        # Check primary features
        assert set(primary) == {'latency', 'smoothness', 'lead_time'}
        
        # Check covariates
        assert set(covariates) == {'neuroticism', 'age'}
    
    def test_no_valid_features_raises_error(self):
        """Test that an error is raised if no valid motion features exist."""
        data = {
            'neuroticism': [1, 2, 3],
            'age': [4, 5, 6],
            'gender': [7, 8, 9],
            'agency_score': [10, 11, 12]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError, match="No valid motion features found"):
            filter_features_for_primary_regression(df, target_col='agency_score')
    
    def test_default_target_column(self):
        """Test default target column behavior."""
        data = {
            'latency': [1, 2, 3],
            'smoothness': [4, 5, 6],
            'neuroticism': [7, 8, 9],
            'custom_target': [10, 11, 12]
        }
        df = pd.DataFrame(data)
        
        # Should use 'agency_score' by default, but it's not in the dataframe
        # So it should fall back to the last column
        primary, covariates = filter_features_for_primary_regression(df)
        
        assert 'latency' in primary
        assert 'smoothness' in primary
        assert 'neuroticism' in covariates

class TestRunCovariateFiltering:
    """Integration tests for the run_covariate_filtering function."""
    
    def test_full_pipeline(self):
        """Test the complete filtering pipeline."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_primary = Path(tmpdir) / 'primary.csv'
            output_covariate = Path(tmpdir) / 'covariate.csv'
            
            # Create test data
            data = {
                'latency': [1.0, 2.0, 3.0, 4.0, 5.0],
                'smoothness': [0.8, 0.9, 0.7, 0.85, 0.95],
                'lead_time': [0.1, 0.2, 0.15, 0.25, 0.3],
                'neuroticism': [3, 4, 2, 5, 3],
                'age': [25, 30, 28, 35, 22],
                'agency_score': [0.7, 0.8, 0.6, 0.9, 0.75]
            }
            pd.DataFrame(data).to_csv(input_path, index=False)
            
            # Run filtering
            report = run_covariate_filtering(
                input_path=str(input_path),
                output_primary_path=str(output_primary),
                output_covariate_path=str(output_covariate)
            )
            
            # Verify outputs exist
            assert output_primary.exists()
            assert output_covariate.exists()
            
            # Verify report content
            assert report['primary_features_count'] == 3
            assert report['covariate_features_count'] == 2
            assert set(report['primary_features']) == {'latency', 'smoothness', 'lead_time'}
            assert set(report['covariate_features']) == {'neuroticism', 'age'}
            
            # Verify primary data
            primary_df = pd.read_csv(output_primary)
            assert set(primary_df.columns) == {'latency', 'smoothness', 'lead_time', 'agency_score'}
            assert len(primary_df) == 5
            
            # Verify covariate data
            covariate_df = pd.read_csv(output_covariate)
            assert set(covariate_df.columns) == {'neuroticism', 'age', 'agency_score'}
            assert len(covariate_df) == 5
            
            # Verify report JSON exists
            report_path = Path(tmpdir) / 'filtering_report.json'
            assert report_path.exists()
            
            with open(report_path) as f:
                json_report = json.load(f)
                assert json_report['primary_features_count'] == 3

    def test_empty_covariates(self):
        """Test handling when there are no covariates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_primary = Path(tmpdir) / 'primary.csv'
            output_covariate = Path(tmpdir) / 'covariate.csv'
            
            # Create data with only motion features
            data = {
                'latency': [1.0, 2.0, 3.0],
                'smoothness': [0.8, 0.9, 0.7],
                'agency_score': [0.7, 0.8, 0.6]
            }
            pd.DataFrame(data).to_csv(input_path, index=False)
            
            report = run_covariate_filtering(
                input_path=str(input_path),
                output_primary_path=str(output_primary),
                output_covariate_path=str(output_covariate)
            )
            
            assert report['covariate_features_count'] == 0
            assert output_covariate.exists()
            covariate_df = pd.read_csv(output_covariate)
            assert list(covariate_df.columns) == ['agency_score']

    def test_missing_input_file(self):
        """Test error handling for missing input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'nonexistent.csv'
            output_primary = Path(tmpdir) / 'primary.csv'
            output_covariate = Path(tmpdir) / 'covariate.csv'
            
            with pytest.raises(FileNotFoundError):
                run_covariate_filtering(
                    input_path=str(input_path),
                    output_primary_path=str(output_primary),
                    output_covariate_path=str(output_covariate)
                )