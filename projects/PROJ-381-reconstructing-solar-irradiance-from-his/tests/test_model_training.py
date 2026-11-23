import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Add code to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.train import (
    load_preprocessed_data,
    prepare_features,
    train_random_forest,
    train_gaussian_process,
    evaluate_model,
    run_loco_cv,
    run_training_pipeline
)

@pytest.fixture
def sample_data():
    """Create a small synthetic dataset mimicking the preprocessed schema for testing."""
    # Create mock data with multiple cycles to test LOCO logic
    np.random.seed(42)
    n_samples = 200
    cycles = [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3] * 16 + [4] * 20 # 16*4 + 20 = 84 rows approx
    # Extend to 200
    while len(cycles) < n_samples:
        cycles.append((len(cycles) % 4) + 1)
    
    data = {
        'date': pd.date_range(start='2000-01-01', periods=len(cycles), freq='D'),
        'gsn': np.random.randint(0, 150, size=len(cycles)),
        'tsi': 1360.5 + np.random.normal(0, 0.5, size=len(cycles)),
        'cycle_id': cycles[:len(cycles)]
    }
    return pd.DataFrame(data)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for test artifacts."""
    tmp_data = tempfile.mkdtemp()
    tmp_models = tempfile.mkdtemp()
    yield Path(tmp_data), Path(tmp_models)
    shutil.rmtree(tmp_data)
    shutil.rmtree(tmp_models)

def test_prepare_features(sample_data):
    """Test that features and targets are correctly extracted."""
    X, y = prepare_features(sample_data)
    assert 'gsn' in X.columns
    assert 'cycle_id' in X.columns
    assert y.name == 'tsi'
    assert len(X) == len(y)

def test_train_random_forest(sample_data):
    """Test RF training does not crash and produces a model."""
    X, y = prepare_features(sample_data)
    model = train_random_forest(X, y)
    assert model is not None
    assert hasattr(model, 'predict')
    # Check hyperparameters
    assert model.max_depth == 10
    assert model.n_estimators == 100

def test_train_gaussian_process(sample_data):
    """Test GP training does not crash and produces a model."""
    X, y = prepare_features(sample_data)
    model = train_gaussian_process(X, y)
    assert model is not None
    assert hasattr(model, 'predict')

def test_evaluate_model(sample_data):
    """Test evaluation returns correct metrics structure."""
    X, y = prepare_features(sample_data)
    model = train_random_forest(X, y)
    metrics = evaluate_model(model, X, y)
    assert 'rmse' in metrics
    assert 'r2' in metrics
    assert isinstance(metrics['rmse'], float)
    assert isinstance(metrics['r2'], float)
    assert metrics['rmse'] >= 0
    assert -1 <= metrics['r2'] <= 1

def test_loco_cv_logic(sample_data, temp_dirs):
    """
    Verify LOCO CV logic:
    1. It iterates through cycles.
    2. It holds out one cycle at a time.
    3. It produces per-cycle metrics.
    4. It selects a model based on performance.
    """
    # Ensure we have at least 3 cycles for a meaningful test
    df = sample_data.copy()
    unique_cycles = df['cycle_id'].unique()
    assert len(unique_cycles) >= 3, "Test data needs at least 3 cycles"

    report = run_loco_cv(df)
    
    # Check report structure
    assert 'methodology' in report
    assert report['methodology'] == "Leave-One-Cycle-Out (LOCO) Cross-Validation"
    assert 'total_cycles' in report
    assert 'random_forest' in report
    assert 'gaussian_process' in report
    assert 'model_selection' in report
    
    # Check per-cycle metrics exist
    assert len(report['random_forest']['per_cycle_metrics']) > 0
    assert len(report['gaussian_process']['per_cycle_metrics']) > 0
    
    # Check a metric entry structure
    first_metric = report['random_forest']['per_cycle_metrics'][0]
    assert 'cycle' in first_metric
    assert 'rmse' in first_metric
    assert 'r2' in first_metric
    
    # Check model selection logic
    assert report['model_selection']['selected_model'] in ['RandomForest', 'GaussianProcess']
    assert 'rationale' in report['model_selection']

def test_run_training_pipeline(temp_dirs, sample_data):
    """Test the full pipeline end-to-end."""
    data_dir, models_dir = temp_dirs
    
    # Save sample data to parquet
    parquet_path = data_dir / "preprocessed_data.parquet"
    sample_data.to_parquet(parquet_path)
    
    # Run pipeline
    paths = run_training_pipeline(data_dir, models_dir)
    
    # Check outputs
    assert 'report' in paths
    assert os.path.exists(paths['report'])
    assert 'random_forest' in paths
    assert os.path.exists(paths['random_forest'])
    assert 'gaussian_process' in paths
    assert os.path.exists(paths['gaussian_process'])
    
    # Verify report content
    with open(paths['report'], 'r') as f:
        report = json.load(f)
    assert 'model_selection' in report
    assert 'per_cycle_metrics' in report['random_forest']