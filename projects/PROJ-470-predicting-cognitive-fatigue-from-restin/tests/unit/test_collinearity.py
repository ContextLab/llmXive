"""
Unit tests for collinearity diagnostics (VIF).

Tests:
1. VIF calculation logic
2. Threshold checking (VIF < 5)
3. File output (vif_diagnostics.log, vif_valid_predictors.json)
4. Error handling for missing files
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from collinearity import (
    setup_logger,
    load_analysis_results,
    calculate_vif,
    run_collinearity_diagnostics,
    save_collinearity_report
)


class TestVIFCalculation:
    """Test VIF calculation logic."""
    
    def test_vif_perfect_collinearity(self):
        """VIF should be very high (or infinite) for perfectly collinear variables."""
        # Create data with perfect collinearity: y = 2*x
        df = pd.DataFrame({
            'x1': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            'x2': [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]  # Perfectly collinear with x1
        })
        
        predictors = ['x1', 'x2']
        vif_results = calculate_vif(df, predictors)
        
        # At least one should have very high VIF
        assert any(v > 100 for v in vif_results.values()), "Perfectly collinear variables should have high VIF"
    
    def test_vif_no_collinearity(self):
        """VIF should be close to 1 for uncorrelated variables."""
        np.random.seed(42)
        df = pd.DataFrame({
            'x1': np.random.randn(100),
            'x2': np.random.randn(100),
            'x3': np.random.randn(100)
        })
        
        predictors = ['x1', 'x2', 'x3']
        vif_results = calculate_vif(df, predictors)
        
        # All VIFs should be close to 1 (typically < 2 for random data)
        for v in vif_results.values():
            assert v < 3.0, f"VIF should be close to 1 for uncorrelated variables, got {v}"
    
    def test_vif_single_predictor(self):
        """VIF calculation should fail or return inf for single predictor."""
        df = pd.DataFrame({'x1': [1, 2, 3, 4, 5]})
        predictors = ['x1']
        
        # This should raise an error or return inf
        with pytest.raises(Exception):
            calculate_vif(df, predictors)


class TestLoadAnalysisResults:
    """Test loading and merging of analysis data."""
    
    def test_missing_complexity_file(self):
        """Should raise FileNotFoundError if complexity metrics missing."""
        with patch('collinearity.Path') as mock_path:
            mock_path.return_value.exists.return_value = False
            with pytest.raises(FileNotFoundError):
                load_analysis_results()
    
    def test_missing_delta_file(self):
        """Should raise FileNotFoundError if delta scores missing."""
        with patch('collinearity.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            # Mock one file to exist, one to not
            call_count = [0]
            def exists_side_effect():
                call_count[0] += 1
                return call_count[0] == 1  # First call True, second False
            
            mock_path.return_value.exists.side_effect = exists_side_effect
            
            with pytest.raises(FileNotFoundError):
                load_analysis_results()
    
    def test_merging_data(self, tmp_path):
        """Test successful merge of complexity and delta data."""
        # Create temporary test files
        complexity_data = pd.DataFrame({
            'participant_id': ['P01', 'P02', 'P03'],
            'channel': ['Fz', 'Fz', 'Fz'],
            'segment_id': ['pre', 'pre', 'pre'],
            'lzc_value': [0.5, 0.6, 0.7],
            'pe_value': [1.2, 1.3, 1.4]
        })
        
        delta_data = pd.DataFrame({
            'participant_id': ['P01', 'P02', 'P03'],
            'Fatigue_Delta': [1.0, 2.0, 3.0]
        })
        
        # Write to temp files
        complexity_path = tmp_path / "complexity_metrics.csv"
        delta_path = tmp_path / "delta_scores.csv"
        complexity_data.to_csv(complexity_path, index=False)
        delta_data.to_csv(delta_path, index=False)
        
        # Patch Path to use temp directory
        with patch('collinearity.Path') as mock_path:
            def path_side_effect(path_str):
                if "complexity_metrics" in str(path_str):
                    return Path(complexity_path)
                elif "delta_scores" in str(path_str):
                    return Path(delta_path)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            mock_path.return_value.exists.return_value = True
            
            merged_df, predictors = load_analysis_results()
            
            assert len(merged_df) == 3
            assert 'Fatigue_Delta' in merged_df.columns
            assert 'Pre_Complexity' in merged_df.columns or 'lzc_value' in merged_df.columns


class TestRunCollinearityDiagnostics:
    """Test the full diagnostics pipeline."""
    
    def test_pass_threshold(self, tmp_path, caplog):
        """Test successful pass when all VIF < 5."""
        # Create mock data with low VIF
        df = pd.DataFrame({
            'Fatigue_Delta': [1.0, 2.0, 3.0, 4.0, 5.0],
            'Pre_Complexity': [0.5, 0.6, 0.7, 0.8, 0.9],
            'age': [25, 30, 35, 40, 45]
        })
        
        with patch('collinearity.load_analysis_results') as mock_load:
            mock_load.return_value = (df, ['Fatigue_Delta', 'Pre_Complexity', 'age'])
            
            with patch('collinearity.Path') as mock_path:
                mock_path.return_value.parent = tmp_path
                mock_path.return_value.exists.return_value = True
                
                result = run_collinearity_diagnostics(MagicMock())
                
                assert result['valid'] is True
                assert 'Fatigue_Delta' in result['predictors']
    
    def test_fail_threshold(self, tmp_path, caplog):
        """Test failure when VIF >= 5."""
        # Create mock data with high VIF (perfectly collinear)
        df = pd.DataFrame({
            'Fatigue_Delta': [1.0, 2.0, 3.0, 4.0, 5.0],
            'Pre_Complexity': [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfectly collinear
            'age': [25, 30, 35, 40, 45]
        })
        
        with patch('collinearity.load_analysis_results') as mock_load:
            mock_load.return_value = (df, ['Fatigue_Delta', 'Pre_Complexity', 'age'])
            
            with patch('collinearity.Path') as mock_path:
                mock_path.return_value.parent = tmp_path
                mock_path.return_value.exists.return_value = True
                
                result = run_collinearity_diagnostics(MagicMock())
                
                assert result['valid'] is False
                assert 'Collinearity violation' in result.get('error', '')


class TestSaveCollinearityReport:
    """Test saving of diagnostic reports."""
    
    def test_save_valid_predictors(self, tmp_path):
        """Test saving vif_valid_predictors.json when all pass."""
        result = {
            'valid': True,
            'predictors': ['Fatigue_Delta', 'Pre_Complexity'],
            'vif_values': {'Fatigue_Delta': 1.5, 'Pre_Complexity': 1.8}
        }
        
        log_path = tmp_path / "vif_diagnostics.log"
        json_path = tmp_path / "vif_valid_predictors.json"
        
        with patch('collinearity.Path') as mock_path:
            def path_side_effect(path_str):
                if "vif_diagnostics" in str(path_str):
                    return Path(log_path)
                elif "vif_valid_predictors" in str(path_str):
                    return Path(json_path)
                return Path(path_str)
            
            mock_path.side_effect = path_side_effect
            mock_path.return_value.parent = tmp_path
            mock_path.return_value.exists.return_value = True
            
            save_collinearity_report(result, MagicMock())
            
            assert json_path.exists()
            with open(json_path) as f:
                saved = json.load(f)
                assert saved['valid'] is True
                assert 'Fatigue_Delta' in saved['predictors']
    
    def test_no_save_on_failure(self, tmp_path):
        """Test that JSON is not saved when VIF check fails."""
        result = {
            'valid': False,
            'error': 'Collinearity violation',
            'predictors': ['Fatigue_Delta', 'Pre_Complexity'],
            'vif_values': {'Fatigue_Delta': 6.5, 'Pre_Complexity': 1.8}
        }
        
        json_path = tmp_path / "vif_valid_predictors.json"
        
        with patch('collinearity.Path') as mock_path:
            mock_path.return_value.parent = tmp_path
            mock_path.return_value.exists.return_value = True
            
            save_collinearity_report(result, MagicMock())
            
            # JSON should not be created for failed checks
            assert not json_path.exists()


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    def test_full_pipeline_pass(self, tmp_path):
        """Test full pipeline with data that passes VIF check."""
        # Create realistic test data
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            'Fatigue_Delta': np.random.randn(n),
            'Pre_Complexity': np.random.randn(n) * 0.5 + 0.5,
            'age': np.random.randint(20, 60, n)
        })
        
        with patch('collinearity.load_analysis_results') as mock_load:
            mock_load.return_value = (df, ['Fatigue_Delta', 'Pre_Complexity', 'age'])
            
            log_path = tmp_path / "vif_diagnostics.log"
            json_path = tmp_path / "vif_valid_predictors.json"
            
            with patch('collinearity.Path') as mock_path:
                def path_side_effect(path_str):
                    if "vif_diagnostics" in str(path_str):
                        return Path(log_path)
                    elif "vif_valid_predictors" in str(path_str):
                        return Path(json_path)
                    return Path(path_str)
                
                mock_path.side_effect = path_side_effect
                mock_path.return_value.parent = tmp_path
                mock_path.return_value.exists.return_value = True
                
                logger = setup_logger("test_integration")
                result = run_collinearity_diagnostics(logger)
                save_collinearity_report(result, logger)
                
                # Verify outputs
                assert result['valid'] is True
                assert json_path.exists()
                assert log_path.exists()
    
    def test_full_pipeline_fail(self, tmp_path):
        """Test full pipeline with data that fails VIF check."""
        # Create data with collinearity
        n = 50
        df = pd.DataFrame({
            'Fatigue_Delta': np.random.randn(n),
            'Pre_Complexity': np.random.randn(n) * 0.5 + 0.5,
            'age': np.random.randint(20, 60, n),
            'age_duplicate': np.random.randint(20, 60, n)  # Highly correlated
        })
        
        # Force high VIF by making age_duplicate = age + small noise
        df['age_duplicate'] = df['age'] + np.random.randn(n) * 0.1
        
        with patch('collinearity.load_analysis_results') as mock_load:
            mock_load.return_value = (df, ['Fatigue_Delta', 'Pre_Complexity', 'age', 'age_duplicate'])
            
            log_path = tmp_path / "vif_diagnostics.log"
            json_path = tmp_path / "vif_valid_predictors.json"
            
            with patch('collinearity.Path') as mock_path:
                def path_side_effect(path_str):
                    if "vif_diagnostics" in str(path_str):
                        return Path(log_path)
                    elif "vif_valid_predictors" in str(path_str):
                        return Path(json_path)
                    return Path(path_str)
                
                mock_path.side_effect = path_side_effect
                mock_path.return_value.parent = tmp_path
                mock_path.return_value.exists.return_value = True
                
                logger = setup_logger("test_integration_fail")
                result = run_collinearity_diagnostics(logger)
                save_collinearity_report(result, logger)
                
                # Verify failure
                assert result['valid'] is False
                assert not json_path.exists()  # No JSON on failure
                assert log_path.exists()  # Log should still be written