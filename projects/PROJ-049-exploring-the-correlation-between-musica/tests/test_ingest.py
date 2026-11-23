"""
Tests for the ingest module functionality.
"""

import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from code.ingest import (
    load_personality_data,
    load_listening_data,
    merge_dataframes,
    filter_active_users,
    apply_genre_standardization,
    preprocess_merged_data
)


@pytest.fixture
def temp_personality_file():
    """Create a temporary personality data file."""
    data = {
        'user_id': [1, 2, 3, 4, 5],
        'extraversion': [0.8, 0.3, 0.6, 0.9, 0.2],
        'agreeableness': [0.7, 0.4, 0.8, 0.5, 0.9],
        'conscientiousness': [0.6, 0.7, 0.5, 0.8, 0.3],
        'neuroticism': [0.3, 0.8, 0.4, 0.2, 0.7],
        'openness': [0.9, 0.5, 0.7, 0.6, 0.4]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_listening_file():
    """Create a temporary listening data file."""
    data = {
        'user_id': [1, 1, 2, 2, 3, 4, 4, 5, 5],
        'genre': ['rock', 'pop', 'jazz', 'rock', 'classical', 'pop', 'rock', 'jazz', 'pop'],
        'listening_minutes': [120.0, 45.0, 0.0, 80.0, 200.0, 0.0, 150.0, 60.0, 30.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    yield temp_path
    os.unlink(temp_path)


def test_load_personality_data(temp_personality_file):
    """Test loading personality data file."""
    df = load_personality_data(temp_personality_file)
    
    assert len(df) == 5
    assert 'user_id' in df.columns
    assert 'extraversion' in df.columns
    assert 'agreeableness' in df.columns
    assert 'conscientiousness' in df.columns
    assert 'neuroticism' in df.columns
    assert 'openness' in df.columns


def test_load_personality_data_missing_file():
    """Test loading non-existent personality file raises error."""
    with pytest.raises(FileNotFoundError):
        load_personality_data("nonexistent_file.csv")


def test_load_personality_data_missing_columns(temp_personality_file):
    """Test loading file with missing required columns raises error."""
    # Create a file with missing columns
    data = {
        'user_id': [1, 2, 3],
        'extraversion': [0.5, 0.6, 0.7]
    }
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f, index=False)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_personality_data(temp_path)
    finally:
        os.unlink(temp_path)


def test_load_listening_data(temp_listening_file):
    """Test loading listening data file."""
    df = load_listening_data(temp_listening_file)
    
    assert len(df) == 9
    assert 'user_id' in df.columns
    assert 'genre' in df.columns
    assert 'listening_minutes' in df.columns


def test_load_listening_data_missing_file():
    """Test loading non-existent listening file raises error."""
    with pytest.raises(FileNotFoundError):
        load_listening_data("nonexistent_file.csv")


def test_merge_dataframes(temp_personality_file, temp_listening_file):
    """Test merging personality and listening data."""
    personality_df = load_personality_data(temp_personality_file)
    listening_df = load_listening_data(temp_listening_file)
    
    merged = merge_dataframes(personality_df, listening_df)
    
    # Should have records for users 1, 2, 3, 4, 5 (all users in personality have listening data)
    # User 1: 2 records, User 2: 2 records, User 3: 1 record, User 4: 2 records, User 5: 2 records
    assert len(merged) == 9
    assert 'user_id' in merged.columns
    assert 'extraversion' in merged.columns
    assert 'genre' in merged.columns
    assert 'listening_minutes' in merged.columns


def test_filter_active_users(temp_personality_file, temp_listening_file):
    """Test filtering out users with zero listening minutes."""
    personality_df = load_personality_data(temp_personality_file)
    listening_df = load_listening_data(temp_listening_file)
    
    merged = merge_dataframes(personality_df, listening_df)
    
    # Before filtering: 9 records (including user 2 with 0 minutes and user 4 with 0 minutes)
    assert len(merged) == 9
    
    # Filter active users
    active = filter_active_users(merged)
    
    # After filtering: should remove records where listening_minutes <= 0
    # User 2 has one record with 0 minutes, User 4 has one record with 0 minutes
    # So we remove 2 records: 9 - 2 = 7
    assert len(active) == 7
    assert all(active['listening_minutes'] > 0)


def test_apply_genre_standardization(temp_personality_file, temp_listening_file):
    """Test applying genre standardization."""
    personality_df = load_personality_data(temp_personality_file)
    listening_df = load_listening_data(temp_listening_file)
    
    merged = merge_dataframes(personality_df, listening_df)
    active = filter_active_users(merged)
    
    standardized = apply_genre_standardization(active)
    
    assert 'standard_genre' in standardized.columns
    assert len(standardized) == len(active)
    
    # Check that standard_genre is not all null
    assert standardized['standard_genre'].notna().sum() > 0


def test_preprocess_merged_data(temp_personality_file, temp_listening_file):
    """Test full preprocessing pipeline."""
    df = preprocess_merged_data(temp_personality_file, temp_listening_file)
    
    # Should have all personality columns
    assert 'extraversion' in df.columns
    assert 'agreeableness' in df.columns
    assert 'conscientiousness' in df.columns
    assert 'neuroticism' in df.columns
    assert 'openness' in df.columns
    
    # Should have listening columns
    assert 'genre' in df.columns
    assert 'listening_minutes' in df.columns
    
    # Should have standardized genre
    assert 'standard_genre' in df.columns
    
    # Should not have zero listening minutes
    assert all(df['listening_minutes'] > 0)
    
    # Should have fewer records than original listening data due to filtering
    assert len(df) < 9
