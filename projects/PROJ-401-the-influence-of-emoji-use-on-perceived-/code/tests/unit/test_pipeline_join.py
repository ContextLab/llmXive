"""
Unit tests for the pipeline join step (T013).

Tests cover:
- Joining raw data with extracted features
- Handling zero-length text
- Handling encoding errors
- Handling missing columns
- Output validation
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from src.data.pipeline_join import join_raw_with_features
from src.data.loaders import DataUnavailableError

class TestPipelineJoin:
    """Test cases for join_raw_with_features function."""
    
    def test_join_basic(self):
        """Test basic join with valid data."""
        raw_df = pd.DataFrame({
            'message_id': [1, 2, 3],
            'text': ['Hello', 'Hello 😊', 'World'],
            'human_intensity_score': [5.0, 8.0, 3.0]
        })
        
        result = join_raw_with_features(raw_df)
        
        assert len(result) == 3
        assert 'emoji_present' in result.columns
        assert 'emoji_count' in result.columns
        assert 'emoji_types' in result.columns
        assert result.loc[result['message_id'] == 2, 'emoji_present'].iloc[0] is True
        assert result.loc[result['message_id'] == 2, 'emoji_count'].iloc[0] > 0
    
    def test_join_empty_text(self):
        """Test handling of zero-length text."""
        raw_df = pd.DataFrame({
            'message_id': [1, 2],
            'text': ['', 'Hello'],
            'human_intensity_score': [5.0, 8.0]
        })
        
        result = join_raw_with_features(raw_df)
        
        assert len(result) == 2
        assert result.loc[result['message_id'] == 1, 'emoji_present'].iloc[0] is False
        assert result.loc[result['message_id'] == 1, 'emoji_count'].iloc[0] == 0
        assert result.loc[result['message_id'] == 1, 'text_length'].iloc[0] == 0
    
    def test_join_missing_columns(self):
        """Test error handling when required columns are missing."""
        raw_df = pd.DataFrame({
            'message_id': [1, 2],
            'human_intensity_score': [5.0, 8.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            join_raw_with_features(raw_df)
        
        assert "Missing required columns" in str(exc_info.value)
    
    def test_join_empty_dataframe(self):
        """Test error handling when input dataframe is empty."""
        raw_df = pd.DataFrame(columns=['message_id', 'text'])
        
        with pytest.raises(DataUnavailableError):
            join_raw_with_features(raw_df)
    
    def test_join_with_nan_text(self):
        """Test handling of NaN values in text column."""
        raw_df = pd.DataFrame({
            'message_id': [1, 2, 3],
            'text': [None, 'Hello', 'Hello 😊'],
            'human_intensity_score': [5.0, 8.0, 8.0]
        })
        
        result = join_raw_with_features(raw_df)
        
        assert len(result) == 3
        # NaN should be treated as empty string
        assert result.loc[result['message_id'] == 1, 'emoji_present'].iloc[0] is False
        assert result.loc[result['message_id'] == 1, 'emoji_count'].iloc[0] == 0
    
    def test_join_output_file(self):
        """Test that output file is created when path is provided."""
        raw_df = pd.DataFrame({
            'message_id': [1, 2],
            'text': ['Hello', 'Hello 😊'],
            'human_intensity_score': [5.0, 8.0]
        })
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.csv"
            result = join_raw_with_features(raw_df, output_path)
            
            assert output_path.exists()
            saved_df = pd.read_csv(output_path)
            assert len(saved_df) == 2
            assert 'emoji_present' in saved_df.columns
    
    def test_join_multiple_emojis(self):
        """Test handling of multiple emojis in a single text."""
        raw_df = pd.DataFrame({
            'message_id': [1],
            'text': ['Hello 😊👍🎉'],
            'human_intensity_score': [8.0]
        })
        
        result = join_raw_with_features(raw_df)
        
        assert result['emoji_count'].iloc[0] == 3
        assert result['emoji_present'].iloc[0] is True
        assert len(result['emoji_types'].iloc[0]) == 3
    
    def test_join_whitespace_only_text(self):
        """Test handling of whitespace-only text."""
        raw_df = pd.DataFrame({
            'message_id': [1],
            'text': ['   '],
            'human_intensity_score': [5.0]
        })
        
        result = join_raw_with_features(raw_df)
        
        assert result['emoji_present'].iloc[0] is False
        assert result['emoji_count'].iloc[0] == 0
        assert result['text_length'].iloc[0] == 0  # Treated as empty after strip
