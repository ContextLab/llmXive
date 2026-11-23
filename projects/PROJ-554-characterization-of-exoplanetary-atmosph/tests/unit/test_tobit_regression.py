"""
Unit tests for Tobit regression implementation (T027).
"""
import json
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock

# Import functions to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis_tobit import (
    load_retrieval_data,
    prepare_tobit_data,
    run_tobit_regression,
    save_regression_results
)
from config import get_config, ConfigurationError

class TestLoadRetrievalData:
    """Tests for load_retrieval_data function."""
    
    def test_load_existing_file(self, tmp_path):
        """Test loading from existing file."""
        # Create mock data
        mock_data = pd.DataFrame({
            'planet_name': ['p1', 'p2', 'p3'],
            'water_mixing_ratio': [-4.0, -3.5, -4.2],
            'is_upper_limit': [False, False, True],
            'temperature': [1200, 1500, 900],
            'mass': [1.2, 2.1, 0.8],
            'metallicity': [0.1, 0.3, -0.2]
        })
        
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        input_file = processed_dir / "retrieval_results.csv"
        mock_data.to_csv(input_file, index=False)
        
        # Mock config to use temp directory
        with patch('analysis_tobit.get_config') as mock_config:
            mock_config.return_value = {
                "paths": {
                    "processed_data": processed_dir
                }
            }
            
            result = load_retrieval_data()
            
            assert len(result) == 3
            assert 'water_mixing_ratio' in result.columns
            assert result['planet_name'].iloc[0] == 'p1'
    
    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing file raises PipelineError."""
        with patch('analysis_tobit.get_config') as mock_config:
            mock_config.return_value = {
                "paths": {
                    "processed_data": tmp_path
                }
            }
            
            with pytest.raises(Exception):  # PipelineError
                load_retrieval_data()

class TestPrepareTobitData:
    """Tests for prepare_tobit_data function."""
    
    def test_prepare_data_with_all_columns(self):
        """Test data preparation with all required columns."""
        df = pd.DataFrame({
            'planet_name': ['p1', 'p2', 'p3'],
            'water_mixing_ratio': [-4.0, -3.5, -4.2],
            'is_upper_limit': [False, False, True],
            'temperature': [1200, 1500, 900],
            'mass': [1.2, 2.1, 0.8],
            'metallicity': [0.1, 0.3, -0.2]
        })
        
        df_prep, censor_mask = prepare_tobit_data(df)
        
        assert 'duration' in df_prep.columns
        assert 'event' in df_prep.columns
        assert df_prep['event'].sum() == 2  # 2 uncensored
        assert (censor_mask == 0).sum() == 1  # 1 censored
    
    def test_prepare_data_missing_mass(self):
        """Test that missing mass column gets placeholder."""
        df = pd.DataFrame({
            'planet_name': ['p1', 'p2'],
            'water_mixing_ratio': [-4.0, -3.5],
            'is_upper_limit': [False, False],
            'temperature': [1200, 1500],
            'metallicity': [0.1, 0.3]
        })
        
        df_prep, _ = prepare_tobit_data(df)
        
        assert 'mass' in df_prep.columns
        assert all(df_prep['mass'] == 1.0)
    
    def test_missing_required_columns_raises_error(self):
        """Test that missing required columns raise error."""
        df = pd.DataFrame({
            'planet_name': ['p1'],
            'water_mixing_ratio': [-4.0]
        })
        
        with pytest.raises(Exception):
            prepare_tobit_data(df)

class TestRunTobitRegression:
    """Tests for run_tobit_regression function."""
    
    def test_regression_with_sufficient_data(self):
        """Test regression with sufficient data points."""
        # Create mock prepared data
        np.random.seed(42)
        n_samples = 50
        df_prep = pd.DataFrame({
            'duration': np.random.uniform(-5, -3, n_samples),
            'event': np.random.choice([0, 1], n_samples, p=[0.2, 0.8]),
            'temperature': np.random.uniform(800, 1800, n_samples),
            'mass': np.random.uniform(0.5, 3.0, n_samples),
            'metallicity': np.random.uniform(-0.5, 0.5, n_samples)
        })
        
        results = run_tobit_regression(df_prep)
        
        assert 'coefficients' in results
        assert 'p_values' in results
        assert 'concordance_index' in results
        assert 'n_samples' in results
        assert results['n_samples'] == n_samples
        assert 'temperature' in results['coefficients']
    
    def test_regression_with_insufficient_data(self):
        """Test that insufficient data raises error."""
        df_prep = pd.DataFrame({
            'duration': [-4.0, -3.5],
            'event': [1, 1],
            'temperature': [1200, 1500]
        })
        
        with pytest.raises(Exception):
            run_tobit_regression(df_prep)
    
    def test_regression_handles_censored_data(self):
        """Test that regression properly handles censored observations."""
        np.random.seed(42)
        n_samples = 30
        df_prep = pd.DataFrame({
            'duration': np.random.uniform(-5, -3, n_samples),
            'event': np.array([0] * 10 + [1] * 20),  # 10 censored, 20 uncensored
            'temperature': np.random.uniform(800, 1800, n_samples),
            'mass': np.random.uniform(0.5, 3.0, n_samples),
            'metallicity': np.random.uniform(-0.5, 0.5, n_samples)
        })
        
        results = run_tobit_regression(df_prep)
        
        assert results['n_censored'] == 10
        assert results['n_uncensored'] == 20
        assert 'concordance_index' in results

class TestSaveRegressionResults:
    """Tests for save_regression_results function."""
    
    def test_save_results_to_json(self, tmp_path):
        """Test saving results to JSON file."""
        results = {
            'model_type': 'WeibullAFT',
            'n_samples': 50,
            'coefficients': {'temperature': 0.001},
            'p_values': {'temperature': 0.03},
            'concordance_index': 0.75
        }
        
        output_path = tmp_path / "regression_results.json"
        save_regression_results(results, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['model_type'] == 'WeibullAFT'
        assert loaded['n_samples'] == 50
        assert abs(loaded['coefficients']['temperature'] - 0.001) < 1e-6

class TestIntegration:
    """Integration tests for the full Tobit regression pipeline."""
    
    def test_full_pipeline(self, tmp_path):
        """Test the complete pipeline from data loading to result saving."""
        # Create mock retrieval data
        mock_data = pd.DataFrame({
            'planet_name': [f'planet_{i}' for i in range(60)],
            'water_mixing_ratio': np.random.uniform(-5, -3, 60),
            'is_upper_limit': np.random.choice([False, True], 60, p=[0.8, 0.2]),
            'temperature': np.random.uniform(800, 1800, 60),
            'mass': np.random.uniform(0.5, 3.0, 60),
            'metallicity': np.random.uniform(-0.5, 0.5, 60)
        })
        
        # Setup directories
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)
        input_file = processed_dir / "retrieval_results.csv"
        mock_data.to_csv(input_file, index=False)
        
        output_file = processed_dir / "regression_results.json"
        
        # Mock config
        with patch('analysis_tobit.get_config') as mock_config:
            with patch('analysis_tobit.setup_logging'):
                with patch('analysis_tobit.get_config') as mock_cfg:
                    mock_cfg.return_value = {
                        "paths": {
                            "processed_data": processed_dir,
                            "log_dir": tmp_path / "logs"
                        }
                    }
                    
                    # Run the pipeline
                    df = load_retrieval_data()
                    df_prep, _ = prepare_tobit_data(df)
                    results = run_tobit_regression(df_prep)
                    save_regression_results(results, output_file)
                    
                    # Verify output
                    assert output_file.exists()
                    
                    with open(output_file, 'r') as f:
                        saved_results = json.load(f)
                    
                    assert saved_results['n_samples'] == 60
                    assert 'temperature' in saved_results['coefficients']
                    assert 'p_values' in saved_results
                    assert 'concordance_index' in saved_results