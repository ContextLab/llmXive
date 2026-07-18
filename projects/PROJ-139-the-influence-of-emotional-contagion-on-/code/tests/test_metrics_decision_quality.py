import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
from code.data.metrics import (
    compute_agreement_proportion,
    compute_shannon_entropy,
    compute_decision_quality_metrics,
    run_decision_quality_pipeline,
    load_processed_data,
    save_thread_metrics
)

@pytest.fixture
def sample_thread_positive():
    """A thread where all comments are positive."""
    return pd.DataFrame({
        'thread_id': [1, 1, 1, 1],
        'comment_id': [101, 102, 103, 104],
        'compound_sentiment': [0.5, 0.8, 0.2, 0.9],
        'timestamp': ['2023-01-01 10:00:00', '2023-01-01 10:05:00', '2023-01-01 10:10:00', '2023-01-01 10:15:00'],
        'external_validation_score': [0.9, 0.9, 0.9, 0.9]
    })

@pytest.fixture
def sample_thread_mixed():
    """A thread with mixed sentiments."""
    return pd.DataFrame({
        'thread_id': [2, 2, 2, 2],
        'comment_id': [201, 202, 203, 204],
        'compound_sentiment': [0.5, -0.6, 0.1, -0.4],
        'timestamp': ['2023-01-01 10:00:00', '2023-01-01 10:05:00', '2023-01-01 10:10:00', '2023-01-01 10:15:00'],
        'external_validation_score': [0.5, 0.5, 0.5, 0.5]
    })

@pytest.fixture
def sample_thread_empty():
    """An empty thread."""
    return pd.DataFrame(columns=['thread_id', 'comment_id', 'compound_sentiment', 'timestamp'])

def test_agreement_proportion_perfect():
    """Test agreement proportion with all positive sentiments."""
    df = pd.DataFrame({
        'thread_id': [1, 1, 1],
        'compound_sentiment': [0.5, 0.8, 0.2]
    })
    # All > 0, so majority count is 3/3 = 1.0
    assert compute_agreement_proportion(df) == 1.0

def test_agreement_proportion_mixed():
    """Test agreement proportion with mixed sentiments."""
    # 2 positive, 1 negative -> 2/3
    df = pd.DataFrame({
        'thread_id': [1, 1, 1],
        'compound_sentiment': [0.5, -0.6, 0.1]
    })
    assert abs(compute_agreement_proportion(df) - (2/3)) < 1e-6

def test_agreement_proportion_empty():
    """Test agreement proportion with empty dataframe."""
    df = pd.DataFrame(columns=['thread_id', 'compound_sentiment'])
    assert compute_agreement_proportion(df) == 0.0

def test_shannon_entropy_perfect_agreement():
    """Entropy should be 0 if all values are the same sign."""
    # All positive -> one bin with probability 1.0 -> entropy 0
    df = pd.DataFrame({
        'thread_id': [1, 1, 1],
        'compound_sentiment': [0.5, 0.8, 0.2]
    })
    # We compute entropy on counts of signs. All 3 are positive.
    # Counts: [3]. Entropy of [3] -> log2(1) = 0
    assert compute_shannon_entropy([3]) == 0.0

def test_shannon_entropy_max_diversity():
    """Entropy should be higher with balanced signs."""
    # Two positive, two negative -> counts [2, 2] -> probs [0.5, 0.5]
    # Entropy = - (0.5*log2(0.5) + 0.5*log2(0.5)) = 1.0
    assert compute_shannon_entropy([2, 2]) == 1.0

def test_decision_quality_metrics_comprehensive(sample_thread_positive, sample_thread_mixed):
    """Test the full metrics computation for a thread."""
    # Test positive thread
    metrics_pos = compute_decision_quality_metrics(sample_thread_positive)
    assert metrics_pos['agreement_proportion'] == 1.0
    assert metrics_pos['shannon_entropy'] == 0.0
    assert metrics_pos['thread_length'] == 4
    assert metrics_pos['time_to_decision_seconds'] == 900.0 # 15 mins
    assert metrics_pos['external_validation_score'] == 0.9

    # Test mixed thread
    metrics_mix = compute_decision_quality_metrics(sample_thread_mixed)
    # 2 pos, 2 neg -> agreement 0.5
    assert abs(metrics_mix['agreement_proportion'] - 0.5) < 1e-6
    # Entropy for 2 pos, 2 neg -> 1.0
    assert abs(metrics_mix['shannon_entropy'] - 1.0) < 1e-6

def test_run_decision_quality_pipeline_integration():
    """Test the full pipeline with temporary files."""
    # Create sample data
    data = {
        'thread_id': [1, 1, 2, 2, 2],
        'comment_id': [101, 102, 201, 202, 203],
        'compound_sentiment': [0.5, 0.8, -0.6, 0.1, 0.4],
        'timestamp': [
            '2023-01-01 10:00:00', '2023-01-01 10:05:00',
            '2023-01-01 11:00:00', '2023-01-01 11:10:00', '2023-01-01 11:20:00'
        ],
        'external_validation_score': [0.9, 0.9, 0.5, 0.5, 0.5]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        result = run_decision_quality_pipeline(str(input_path), str(output_path))
        
        assert result['status'] == 'success'
        assert result['output_count'] == 2 # Two threads
        assert Path(output_path).exists()
        
        # Verify output content
        output_df = pd.read_csv(output_path)
        assert 'thread_id' in output_df.columns
        assert 'agreement_proportion' in output_df.columns
        assert 'shannon_entropy' in output_df.columns

def test_run_decision_quality_pipeline_empty_input():
    """Test pipeline with empty dataframe."""
    df = pd.DataFrame(columns=['thread_id', 'comment_id', 'compound_sentiment', 'timestamp'])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.csv"
        output_path = Path(tmpdir) / "output.csv"
        
        df.to_csv(input_path, index=False)
        
        result = run_decision_quality_pipeline(str(input_path), str(output_path))
        
        assert result['status'] == 'empty'
        assert result['output_count'] == 0
        assert Path(output_path).exists()

def test_save_thread_metrics():
    """Test saving metrics to CSV."""
    metrics = [
        {'thread_id': 1, 'agreement_proportion': 1.0, 'shannon_entropy': 0.0},
        {'thread_id': 2, 'agreement_proportion': 0.5, 'shannon_entropy': 1.0}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "metrics.csv"
        save_thread_metrics(metrics, str(output_path))
        
        assert Path(output_path).exists()
        df = pd.read_csv(output_path)
        assert len(df) == 2
        assert 'thread_id' in df.columns