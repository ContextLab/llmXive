import pytest
import pandas as pd
import numpy as np
import json
import os
import tempfile
from pathlib import Path

# Import the functions to test
from robustness_validation import load_sensitivity_data, validate_against_sc003

class TestLoadSensitivityData:
    def test_load_valid_data(self):
        """Test loading valid sensitivity data"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("min_cluster_size,min_samples,region_size,mean_correlation,robustness_score\n")
            f.write("5,5,100,0.3,0.85\n")
            f.write("10,10,80,0.35,0.90\n")
            temp_path = f.name
        
        try:
            df = load_sensitivity_data(temp_path)
            assert len(df) == 2
            assert 'robustness_score' in df.columns
            assert df['robustness_score'].iloc[0] == 0.85
        finally:
            os.unlink(temp_path)
    
    def test_missing_file(self):
        """Test loading from non-existent file"""
        with pytest.raises(FileNotFoundError):
            load_sensitivity_data("nonexistent_file.csv")
    
    def test_missing_columns(self):
        """Test loading data with missing required columns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("min_cluster_size,min_samples\n")
            f.write("5,5\n")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                load_sensitivity_data(temp_path)
        finally:
            os.unlink(temp_path)

class TestValidateAgainstSC003:
    def test_all_pass(self):
        """Test validation when all configurations pass"""
        df = pd.DataFrame({
            'min_cluster_size': [5, 10, 15],
            'min_samples': [5, 10, 15],
            'region_size': [100, 80, 90],
            'mean_correlation': [0.3, 0.35, 0.32],
            'robustness_score': [0.85, 0.90, 0.88]
        })
        
        result = validate_against_sc003(df, threshold=0.7)
        
        assert result['sc003_compliant'] is True
        assert result['successful_sweeps'] == 3
        assert result['failed_sweeps'] == 0
        assert result['mean_robustness'] > 0.8
    
    def test_some_fail(self):
        """Test validation when some configurations fail"""
        df = pd.DataFrame({
            'min_cluster_size': [5, 10, 15],
            'min_samples': [5, 10, 15],
            'region_size': [100, 80, 90],
            'mean_correlation': [0.3, 0.35, 0.32],
            'robustness_score': [0.85, 0.50, 0.88]
        })
        
        result = validate_against_sc003(df, threshold=0.7)
        
        assert result['sc003_compliant'] is False
        assert result['successful_sweeps'] == 2
        assert result['failed_sweeps'] == 1
    
    def test_empty_dataframe(self):
        """Test validation with empty dataframe"""
        df = pd.DataFrame(columns=['min_cluster_size', 'min_samples', 'region_size', 'mean_correlation', 'robustness_score'])
        
        result = validate_against_sc003(df, threshold=0.7)
        
        assert result['sc003_compliant'] is False
        assert "No sensitivity data available" in result['summary']
    
    def test_no_robustness_scores(self):
        """Test validation with no valid robustness scores"""
        df = pd.DataFrame({
            'min_cluster_size': [5, 10],
            'min_samples': [5, 10],
            'region_size': [100, 80],
            'mean_correlation': [0.3, 0.35],
            'robustness_score': [None, None]
        })
        
        result = validate_against_sc003(df, threshold=0.7)
        
        assert result['sc003_compliant'] is False
        assert "No valid robustness scores" in result['summary']
    
    def test_threshold_boundary(self):
        """Test validation at exact threshold boundary"""
        df = pd.DataFrame({
            'min_cluster_size': [5],
            'min_samples': [5],
            'region_size': [100],
            'mean_correlation': [0.3],
            'robustness_score': [0.7]  # Exactly at threshold
        })
        
        result = validate_against_sc003(df, threshold=0.7)
        
        assert result['sc003_compliant'] is True
        assert result['successful_sweeps'] == 1

class TestIntegration:
    def test_full_pipeline(self):
        """Test full validation pipeline with temp files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "sensitivity_analysis.csv"
            output_path = Path(tmpdir) / "robustness_validation.json"
            
            # Create test data
            df = pd.DataFrame({
                'min_cluster_size': [5, 10, 15, 20],
                'min_samples': [5, 10, 15, 5],
                'region_size': [100, 80, 90, 95],
                'mean_correlation': [0.3, 0.35, 0.32, 0.31],
                'robustness_score': [0.85, 0.90, 0.88, 0.72]
            })
            df.to_csv(input_path, index=False)
            
            # Run validation
            result = validate_against_sc003(df, threshold=0.7)
            
            # Save result
            with open(output_path, 'w') as f:
                json.dump(result, f)
            
            # Verify output
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_result = json.load(f)
            
            assert saved_result['sc003_compliant'] is True
            assert saved_result['total_sweeps'] == 4
            assert saved_result['successful_sweeps'] == 4