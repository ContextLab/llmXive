"""
Unit tests for edge_case_handler module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.utils.edge_case_handler import (
    detect_empty_or_short_texts,
    detect_missing_ratings,
    handle_edge_cases,
    log_exclusions,
    get_exclusion_summary
)

@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'conversation_id': ['conv1', 'conv2', 'conv3', 'conv4', 'conv5'],
        'text': [
            'This is a long enough text for testing purposes.',
            'Hi',  # Too short (2 words)
            '',  # Empty
            'Another valid text with more than five words here.',
            'Short'  # Too short (1 word)
        ],
        'authenticity_score': [4.5, 3.2, np.nan, 4.0, 3.8]  # conv3 has missing rating
    })

def test_detect_empty_or_short_texts(sample_dataframe):
    """Test detection of empty and short texts."""
    exclusions = detect_empty_or_short_texts(sample_dataframe, 'text', min_words=5)
    
    assert len(exclusions) == 3  # conv2, conv3 (empty), conv5
    
    reasons = [ex['reason'] for ex in exclusions]
    assert 'short_text_2_words' in reasons
    assert 'empty_text' in reasons
    assert 'short_text_1_words' in reasons

def test_detect_missing_ratings(sample_dataframe):
    """Test detection of missing ratings."""
    exclusions = detect_missing_ratings(sample_dataframe, 'authenticity_score')
    
    assert len(exclusions) == 1
    assert exclusions[0]['reason'] == 'missing_rating'
    assert exclusions[0]['conversation_id'] == 'conv3'

def test_handle_edge_cases(sample_dataframe):
    """Test the main edge case handling function."""
    filtered_df, exclusions = handle_edge_cases(
        sample_dataframe, 
        text_column='text', 
        rating_column='authenticity_score',
        min_words=5,
        log_to_file=False
    )
    
    # Should exclude conv2 (short), conv3 (empty + missing rating), conv5 (short)
    assert len(filtered_df) == 2
    assert set(filtered_df['conversation_id'].tolist()) == {'conv1', 'conv4'}
    
    # Should have 3 exclusions (conv2, conv3, conv5)
    assert len(exclusions) == 3

def test_handle_edge_cases_with_logging(sample_dataframe, tmp_path):
    """Test that exclusions are logged to file."""
    # Temporarily change log file location for testing
    import src.utils.edge_case_handler as module
    original_log_file = module.LOG_FILE
    module.LOG_FILE = tmp_path / "test_exclusion_log.csv"
    
    try:
        filtered_df, exclusions = handle_edge_cases(
            sample_dataframe, 
            text_column='text', 
            rating_column='authenticity_score',
            min_words=5,
            log_to_file=True
        )
        
        # Check that log file was created
        assert module.LOG_FILE.exists()
        
        # Check log contents
        log_df = get_exclusion_summary()
        assert len(log_df) == 3
    finally:
        # Restore original log file
        module.LOG_FILE = original_log_file

def test_get_exclusion_summary_no_log():
    """Test get_exclusion_summary when log file doesn't exist."""
    # Remove log file if it exists
    log_path = Path("data/derived/exclusion_log.csv")
    if log_path.exists():
        log_path.unlink()
    
    result = get_exclusion_summary()
    assert result is None

def test_empty_dataframe():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame(columns=['conversation_id', 'text', 'authenticity_score'])
    
    filtered_df, exclusions = handle_edge_cases(empty_df, 'text', 'authenticity_score')
    
    assert len(filtered_df) == 0
    assert len(exclusions) == 0

def test_dataframe_with_no_text_column():
    """Test handling of DataFrame without text column."""
    df = pd.DataFrame({
        'conversation_id': ['conv1'],
        'authenticity_score': [4.5]
    })
    
    filtered_df, exclusions = handle_edge_cases(df, 'text', 'authenticity_score')
    
    # Should not exclude anything since text column doesn't exist
    assert len(filtered_df) == 1
    assert len(exclusions) == 0

def test_dataframe_with_no_rating_column():
    """Test handling of DataFrame without rating column."""
    df = pd.DataFrame({
        'conversation_id': ['conv1'],
        'text': ['This is a valid text with more than five words']
    })
    
    filtered_df, exclusions = handle_edge_cases(df, 'text', 'authenticity_score')
    
    # Should not exclude anything since rating column doesn't exist
    assert len(filtered_df) == 1
    assert len(exclusions) == 0
