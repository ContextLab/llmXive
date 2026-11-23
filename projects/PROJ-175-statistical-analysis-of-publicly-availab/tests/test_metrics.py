import os
import json
import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from evaluation.metrics import (
    load_test_data,
    load_models,
    get_predictions,
    calculate_metrics,
    generate_calibration_plot
)

@pytest.fixture
def sample_test_data(tmp_path):
    """Create a sample test dataset."""
    data = {
        'log_co_occurrence': np.random.rand(100),
        'flavor_similarity': np.random.rand(100),
        'functional_role': np.random.randint(0, 3, 100),
        'compatibility_label': np.random.randint(0, 2, 100)
    }
    df = pd.DataFrame(data)
    test_file = tmp_path / "test_set.parquet"
    df.to_parquet(test_file)
    return test_file

@pytest.fixture
def sample_models(tmp_path):
    """Create sample model results."""
    models = {
        'logistic': {
            'coefficients': {
                'log_co_occurrence': 0.5,
                'flavor_similarity': 0.3,
                'functional_role': -0.2
            },
            'intercept': 0.1
        },
        'bayesian': {
            'posterior_mean': {
                'log_co_occurrence': 0.4,
                'flavor_similarity': 0.35,
                'functional_role': -0.15
            },
            'intercept_mean': 0.12
        }
    }
    
    log_file = tmp_path / "logistic_results.json"
    with open(log_file, 'w') as f:
        json.dump(models['logistic'], f)
    
    bayes_file = tmp_path / "bayesian_results.json"
    with open(bayes_file, 'w') as f:
        json.dump(models['bayesian'], f)
    
    return tmp_path

def test_load_test_data(sample_test_data, tmp_path):
    """Test loading test data."""
    # Temporarily change working directory
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Move test data to expected location
        expected_path = Path("data/processed/test_set.parquet")
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        sample_test_data.rename(expected_path)
        
        df = load_test_data()
        assert len(df) == 100
        assert 'compatibility_label' in df.columns
    finally:
        os.chdir(original_cwd)

def test_get_predictions(sample_test_data, sample_models, tmp_path):
    """Test prediction generation."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Setup files
        expected_test_path = Path("data/processed/test_set.parquet")
        expected_test_path.parent.mkdir(parents=True, exist_ok=True)
        sample_test_data.rename(expected_test_path)
        
        expected_log_path = Path("data/final/logistic_results.json")
        expected_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(expected_log_path, 'w') as f:
            json.dump(sample_models['logistic'], f)
        
        expected_bayes_path = Path("data/final/bayesian_results.json")
        with open(expected_bayes_path, 'w') as f:
            json.dump(sample_models['bayesian'], f)
        
        df = load_test_data()
        models = load_models()
        predictions, y_true = get_predictions(df, models)
        
        assert 'logistic' in predictions
        assert 'bayesian' in predictions
        assert len(predictions['logistic']) == len(df)
        assert len(predictions['bayesian']) == len(df)
        
        # Check predictions are probabilities (0-1)
        assert all(0 <= p <= 1 for p in predictions['logistic'])
        assert all(0 <= p <= 1 for p in predictions['bayesian'])
    finally:
        os.chdir(original_cwd)

def test_calculate_metrics(sample_test_data, sample_models, tmp_path):
    """Test metric calculation."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Setup files
        expected_test_path = Path("data/processed/test_set.parquet")
        expected_test_path.parent.mkdir(parents=True, exist_ok=True)
        sample_test_data.rename(expected_test_path)
        
        expected_log_path = Path("data/final/logistic_results.json")
        expected_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(expected_log_path, 'w') as f:
            json.dump(sample_models['logistic'], f)
        
        df = load_test_data()
        models = load_models()
        predictions, y_true = get_predictions(df, models)
        
        metrics = calculate_metrics(predictions, y_true)
        
        assert 'logistic' in metrics
        assert 'auc' in metrics['logistic']
        assert 'precision' in metrics['logistic']
        assert 'recall' in metrics['logistic']
        
        # AUC should be between 0 and 1
        assert 0 <= metrics['logistic']['auc'] <= 1
    finally:
        os.chdir(original_cwd)

def test_generate_calibration_plot(sample_test_data, sample_models, tmp_path):
    """Test calibration plot generation."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Setup files
        expected_test_path = Path("data/processed/test_set.parquet")
        expected_test_path.parent.mkdir(parents=True, exist_ok=True)
        sample_test_data.rename(expected_test_path)
        
        expected_log_path = Path("data/final/logistic_results.json")
        expected_log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(expected_log_path, 'w') as f:
            json.dump(sample_models['logistic'], f)
        
        df = load_test_data()
        models = load_models()
        predictions, y_true = get_predictions(df, models)
        
        # Create docs directory
        Path("docs").mkdir(exist_ok=True)
        
        plot_path = generate_calibration_plot(predictions, y_true)
        
        assert plot_path.exists()
        assert str(plot_path).endswith("calibration_plot.png")
    finally:
        os.chdir(original_cwd)