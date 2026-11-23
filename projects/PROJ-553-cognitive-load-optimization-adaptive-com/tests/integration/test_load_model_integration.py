import os
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import pickle
from scipy.stats import pearsonr

# Import functions from the module under test
from code.train_load_model import (
    ensure_golden_set_validity,
    engineer_features,
    check_collinearity,
    train_model,
    check_model_size,
    save_model,
    save_metrics,
    main,
    TARGET_CORRELATION,
    MAX_MODEL_SIZE_MB,
    GOLDEN_SET_PATH,
    MODEL_OUTPUT_PATH,
    METRICS_OUTPUT_PATH
)

@pytest.fixture
def sample_golden_set(tmp_path):
    """Create a sample golden set for testing."""
    data = {
        'interaction_id': [f'int_{i}' for i in range(100)],
        'expert_load_score': np.random.uniform(0, 100, 100),
        'response_latency': np.random.uniform(0.5, 30.0, 100),
        'error_flag': np.random.randint(0, 2, 100),
        'hint_request': np.random.randint(0, 5, 100),
        'pause_duration': np.random.uniform(0.1, 5.0, 100)
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "golden_set.csv"
    df.to_csv(output_path, index=False)
    return str(output_path)

@pytest.fixture
def mock_processed_data(sample_golden_set):
    """Load and process the golden set."""
    golden_set = pd.read_csv(sample_golden_set)
    return engineer_features(golden_set)

def test_ensure_golden_set_validity_valid(sample_golden_set):
    """Test validation with a valid golden set."""
    result = ensure_golden_set_validity(sample_golden_set)
    assert len(result) >= 50
    assert 'expert_load_score' in result.columns
    assert result['expert_load_score'].between(0, 100).all()

def test_ensure_golden_set_validity_missing_file(tmp_path):
    """Test validation with missing file."""
    with pytest.raises(FileNotFoundError):
        ensure_golden_set_validity(str(tmp_path / "nonexistent.csv"))

def test_ensure_golden_set_validity_insufficient_rows(tmp_path):
    """Test validation with insufficient rows."""
    data = {
        'interaction_id': [f'int_{i}' for i in range(20)],
        'expert_load_score': np.random.uniform(0, 100, 20)
    }
    df = pd.DataFrame(data)
    output_path = tmp_path / "small_golden_set.csv"
    df.to_csv(output_path, index=False)
    
    with pytest.raises(ValueError, match="at least 50 rows"):
        ensure_golden_set_validity(str(output_path))

def test_engineer_features(mock_processed_data):
    """Test feature engineering."""
    assert 'log_latency' in mock_processed_data.columns or 'response_latency' in mock_processed_data.columns
    assert not mock_processed_data.isna().any().any()

def test_check_collinearity(mock_processed_data):
    """Test collinearity check."""
    result = check_collinearity(mock_processed_data, 'expert_load_score')
    assert 'highly_collinear' in result
    assert 'vif_scores' in result
    assert isinstance(result['highly_collinear'], bool)

def test_train_model(mock_processed_data):
    """Test model training."""
    from sklearn.model_selection import train_test_split
    
    train_df, valid_df = train_test_split(
        mock_processed_data, 
        test_size=0.2, 
        random_state=42
    )
    
    model, metrics = train_model(train_df, valid_df)
    
    assert model is not None
    assert 'pearson_correlation' in metrics
    assert 'rmse' in metrics
    assert metrics['n_train'] > 0
    assert metrics['n_valid'] > 0

def test_check_model_size(tmp_path, mock_processed_data):
    """Test model size check."""
    from sklearn.model_selection import train_test_split
    import lightgbm as lgb
    
    train_df, valid_df = train_test_split(
        mock_processed_data, 
        test_size=0.2, 
        random_state=42
    )
    
    model, _ = train_model(train_df, valid_df)
    
    model_path = str(tmp_path / "test_model.pkl")
    result = check_model_size(model, model_path)
    
    assert result is True
    assert os.path.exists(model_path)
    
    # Cleanup
    if os.path.exists(model_path):
        os.remove(model_path)

def test_full_pipeline_integration(sample_golden_set, tmp_path):
    """Test the full pipeline integration."""
    import json
    
    # Override paths to use temp directory
    original_golden_path = GOLDEN_SET_PATH
    original_model_path = MODEL_OUTPUT_PATH
    original_metrics_path = METRICS_OUTPUT_PATH
    
    try:
        # Update global paths for this test
        import code.train_load_model as module
        module.GOLDEN_SET_PATH = sample_golden_set
        module.MODEL_OUTPUT_PATH = str(tmp_path / "load_model.pkl")
        module.METRICS_OUTPUT_PATH = str(tmp_path / "model_metrics.json")
        
        # Run main
        main()
        
        # Verify outputs
        assert os.path.exists(module.MODEL_OUTPUT_PATH)
        assert os.path.exists(module.METRICS_PATH)
        
        # Check model file size
        model_size_mb = os.path.getsize(module.MODEL_OUTPUT_PATH) / (1024 * 1024)
        assert model_size_mb <= MAX_MODEL_SIZE_MB, f"Model too large: {model_size_mb}MB"
        
        # Check metrics file
        with open(module.METRICS_PATH, 'r') as f:
            metrics = json.load(f)
        
        assert 'pearson_correlation' in metrics
        assert metrics['pearson_correlation'] >= TARGET_CORRELATION, \
            f"Correlation {metrics['pearson_correlation']} below target {TARGET_CORRELATION}"
        
    finally:
        # Restore original paths
        module.GOLDEN_SET_PATH = original_golden_path
        module.MODEL_OUTPUT_PATH = original_model_path
        module.METRICS_OUTPUT_PATH = original_metrics_path

def test_model_performance_threshold(sample_golden_set, tmp_path):
    """Test that model meets performance threshold."""
    # This test verifies the correlation threshold is enforced
    import code.train_load_model as module
    
    original_golden_path = GOLDEN_SET_PATH
    original_model_path = MODEL_OUTPUT_PATH
    original_metrics_path = METRICS_OUTPUT_PATH
    
    try:
        module.GOLDEN_SET_PATH = sample_golden_set
        module.MODEL_OUTPUT_PATH = str(tmp_path / "load_model.pkl")
        module.METRICS_OUTPUT_PATH = str(tmp_path / "model_metrics.json")
        
        # Run main
        main()
        
        # Load metrics
        with open(module.METRICS_OUTPUT_PATH, 'r') as f:
            metrics = json.load(f)
        
        assert metrics['pearson_correlation'] >= TARGET_CORRELATION
        
    finally:
        module.GOLDEN_SET_PATH = original_golden_path
        module.MODEL_OUTPUT_PATH = original_model_path
        module.METRICS_OUTPUT_PATH = original_metrics_path
