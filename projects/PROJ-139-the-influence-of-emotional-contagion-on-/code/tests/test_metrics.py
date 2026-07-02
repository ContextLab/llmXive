"""
Unit tests for T015: Emotional contagion index computation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from code.data.metrics import (
    calculate_sentiment_slope,
    calculate_contagion_index,
    compute_thread_level_metrics,
    compute_aggregate_contagion,
    MIN_REPLIES_FOR_ANALYSIS
)


@pytest.fixture
def sample_thread_with_sufficient_replies():
    """Create a sample thread with 10 replies for testing."""
    data = {
        'thread_id': ['thread_1'] * 11,
        'position': list(range(11)),
        'sentiment_compound': [
            0.5,  # seed post
            0.3,  # reply 1
            0.2,  # reply 2
            0.1,  # reply 3
            0.0,  # reply 4
            -0.1, # reply 5
            -0.2, # reply 6
            -0.3, # reply 7
            -0.4, # reply 8
            -0.5, # reply 9
            -0.6  # reply 10
        ]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_thread_with_insufficient_replies():
    """Create a sample thread with only 3 replies."""
    data = {
        'thread_id': ['thread_2'] * 4,
        'position': list(range(4)),
        'sentiment_compound': [
            0.5,  # seed post
            0.3,  # reply 1
            0.2,  # reply 2
            0.1   # reply 3
        ]
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_thread_with_no_replies():
    """Create a sample thread with no replies."""
    data = {
        'thread_id': ['thread_3'] * 1,
        'position': [0],
        'sentiment_compound': [0.5]
    }
    return pd.DataFrame(data)


def test_calculate_sentiment_slope_sufficient_data(sample_thread_with_sufficient_replies):
    """Test slope calculation with sufficient replies."""
    slope = calculate_sentiment_slope(sample_thread_with_sufficient_replies)
    assert not np.isnan(slope), "Slope should be calculated for sufficient data"
    # With decreasing sentiment, slope should be negative
    assert slope < 0, "Slope should be negative for decreasing sentiment"


def test_calculate_sentiment_slope_insufficient_data(sample_thread_with_insufficient_replies):
    """Test slope calculation returns NaN for insufficient replies."""
    slope = calculate_sentiment_slope(sample_thread_with_insufficient_replies)
    assert np.isnan(slope), "Slope should be NaN for insufficient replies"


def test_calculate_contagion_index_sufficient_data(sample_thread_with_sufficient_replies):
    """Test contagion index calculation with sufficient replies."""
    result = calculate_contagion_index(sample_thread_with_sufficient_replies)
    
    assert result is not None, "Result should not be None for sufficient data"
    assert 'contagion_index' in result
    assert 'seed_sentiment' in result
    assert 'slope' in result
    assert 'num_replies' in result
    assert result['num_replies'] >= MIN_REPLIES_FOR_ANALYSIS


def test_calculate_contagion_index_insufficient_data(sample_thread_with_insufficient_replies):
    """Test contagion index returns None for insufficient replies."""
    result = calculate_contagion_index(sample_thread_with_insufficient_replies)
    assert result is None, "Result should be None for insufficient replies"


def test_calculate_contagion_index_no_replies(sample_thread_with_no_replies):
    """Test contagion index returns None for threads with no replies."""
    result = calculate_contagion_index(sample_thread_with_no_replies)
    assert result is None, "Result should be None for threads with no replies"


def test_compute_thread_level_metrics():
    """Test thread-level metrics computation across multiple threads."""
    # Create a mixed dataset
    data = {
        'thread_id': ['t1'] * 11 + ['t2'] * 4 + ['t3'] * 6,
        'position': list(range(11)) + list(range(4)) + list(range(6)),
        'sentiment_compound': (
            [0.5] + [0.3, 0.2, 0.1, 0.0, -0.1, -0.2, -0.3, -0.4, -0.5, -0.6] +  # t1: 10 replies
            [0.5, 0.3, 0.2, 0.1] +  # t2: 3 replies
            [0.5, 0.4, 0.3, 0.2, 0.1, 0.0]  # t3: 5 replies
        )
    }
    df = pd.DataFrame(data)
    
    metrics_df, excluded = compute_thread_level_metrics(df)
    
    # t1 and t3 should pass (>=5 replies), t2 should be excluded
    assert len(metrics_df) == 2, "Should have 2 threads with sufficient replies"
    assert len(excluded) == 1, "Should have 1 excluded thread"
    assert 't2' in excluded, "t2 should be in excluded list"
    
    # Check that metrics are computed
    assert 'contagion_index' in metrics_df.columns
    assert 'seed_sentiment' in metrics_df.columns
    assert 'slope' in metrics_df.columns


def test_compute_aggregate_contagion():
    """Test aggregate contagion computation."""
    # Create a dataset with multiple threads showing a pattern
    # We'll create threads where seed sentiment correlates with slope
    threads = []
    for i in range(10):
        seed_sentiment = -0.5 + i * 0.1  # -0.5 to 0.4
        # Create replies that follow a slope related to seed sentiment
        replies = []
        for j in range(1, 11):  # 10 replies
            # Slope becomes more negative as seed sentiment increases
            slope_factor = -seed_sentiment * 0.5
            reply_sentiment = seed_sentiment + j * slope_factor * 0.1
            replies.append(reply_sentiment)
        
        thread_data = {
            'thread_id': [f't{i}'] * 11,
            'position': list(range(11)),
            'sentiment_compound': [seed_sentiment] + replies
        }
        threads.append(pd.DataFrame(thread_data))
    
    df = pd.concat(threads, ignore_index=True)
    
    result = compute_aggregate_contagion(df)
    
    assert 'correlation' in result
    assert 'p_value' in result
    assert 'num_threads' in result
    assert result['num_threads'] == 10
    assert not np.isnan(result['correlation']), "Correlation should be calculable"


def test_min_replies_constant():
    """Test that the minimum replies constant is set correctly."""
    assert MIN_REPLIES_FOR_ANALYSIS == 5, "Minimum replies should be 5"


def test_empty_dataframe():
    """Test handling of empty dataframe."""
    df = pd.DataFrame(columns=['thread_id', 'position', 'sentiment_compound'])
    
    metrics_df, excluded = compute_thread_level_metrics(df)
    
    assert metrics_df.empty
    assert len(excluded) == 0