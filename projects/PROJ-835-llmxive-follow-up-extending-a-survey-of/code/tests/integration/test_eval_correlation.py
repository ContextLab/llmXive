import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models.eval import (
    load_predictions,
    load_anomaly_scores,
    calculate_correlation_and_hypothesis_test,
    save_correlation_results
)

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_anomaly_scores(temp_data_dir):
    """Generate a sample anomaly_scores.parquet file."""
    n_samples = 100
    data = {
        'sample_id': [f"sample_{i}" for i in range(n_samples)],
        'mahalanobis_distance': np.random.rand(n_samples) * 10,
        'label': np.random.randint(0, 2, n_samples)
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / "anomaly_scores.parquet"
    df.to_parquet(path)
    return path

@pytest.fixture
def sample_predictions(temp_data_dir):
    """Generate a sample predictions.csv file."""
    n_samples = 100
    data = {
        'sample_id': [f"sample_{i}" for i in range(n_samples)],
        'prediction': np.random.randint(0, 2, n_samples),
        'probability': np.random.rand(n_samples),
        'label': np.random.randint(0, 2, n_samples)
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / "predictions.csv"
    df.to_csv(path, index=False)
    return path

def test_load_anomaly_scores(sample_anomaly_scores):
    """Test loading anomaly scores from parquet."""
    df = load_anomaly_scores(sample_anomaly_scores)
    assert 'mahalanobis_distance' in df.columns
    assert 'label' in df.columns
    assert len(df) == 100

def test_load_predictions(sample_predictions):
    """Test loading predictions from csv."""
    df = load_predictions(sample_predictions)
    assert 'prediction' in df.columns
    assert 'probability' in df.columns
    assert 'label' in df.columns
    assert len(df) == 100

def test_calculate_correlation_and_hypothesis_test(sample_anomaly_scores):
    """Test correlation calculation logic."""
    df = load_anomaly_scores(sample_anomaly_scores)
    r, p_value, stats = calculate_correlation_and_hypothesis_test(df)

    assert isinstance(r, float)
    assert isinstance(p_value, float)
    assert -1.0 <= r <= 1.0
    assert 0.0 <= p_value <= 1.0
    assert 'sample_size' in stats
    assert stats['sample_size'] == 100

def test_save_correlation_results(temp_data_dir, sample_anomaly_scores):
    """Test saving correlation results to JSON."""
    df = load_anomaly_scores(sample_anomaly_scores)
    _, _, stats = calculate_correlation_and_hypothesis_test(df)
    output_path = temp_data_dir / "correlation.json"

    save_correlation_results(stats, output_path)

    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded_stats = json.load(f)
    assert 'correlation_coefficient' in loaded_stats
    assert 'p_value' in loaded_stats

def test_correlation_with_known_data(temp_data_dir):
    """Test correlation with data that has a known relationship."""
    # Create data with a strong positive correlation
    n = 50
    distances = np.linspace(0, 10, n)
    labels = (distances > 5).astype(int) # Step function, high correlation expected
    
    data = {
        'sample_id': [f"sample_{i}" for i in range(n)],
        'mahalanobis_distance': distances,
        'label': labels
    }
    df = pd.DataFrame(data)
    path = temp_data_dir / "strong_corr.parquet"
    df.to_parquet(path)

    r, p_value, stats = calculate_correlation_and_hypothesis_test(df)

    # With a step function, correlation might not be perfect but should be significant
    assert stats['threshold_met'] == True # p < 0.05 should be true here
    logger = logging.getLogger(__name__)
    logger.info(f"Known data test: r={r}, p={p_value}")