import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cue_matching import normalize_text, normalize_cues, build_inverse_index, match_cues, resolve_collisions

class TestNormalizeText:
    """Unit tests for text normalization logic (T019)."""

    def test_lowercase_conversion(self):
        """Test that text is converted to lowercase."""
        assert normalize_text("Hello World") == "hello world"
        assert normalize_text("HELLO") == "hello"

    def test_punctuation_removal(self):
        """Test that punctuation is removed."""
        assert normalize_text("Hello, World!") == "hello world"
        assert normalize_text("It's a test.") == "its a test"

    def test_whitespace_collapsing(self):
        """Test that multiple whitespace is collapsed."""
        assert normalize_text("Hello   World") == "hello world"
        assert normalize_text("  Hello World  ") == "hello world"

    def test_empty_string(self):
        """Test handling of empty strings."""
        assert normalize_text("") == ""

    def test_non_string_input(self):
        """Test handling of non-string input."""
        assert normalize_text(123) == ""
        assert normalize_text(None) == ""

class TestNormalizeCues:
    """Unit tests for cue normalization."""

    def test_normalize_cues_dataframe(self):
        """Test that normalize_cues adds normalized_cue column."""
        df = pd.DataFrame({'cue_text': ['Hello World', 'Test, Case!']})
        result = normalize_cues(df)
        
        assert 'normalized_cue' in result.columns
        assert result.loc[0, 'normalized_cue'] == "hello world"
        assert result.loc[1, 'normalized_cue'] == "test case"

    def test_normalize_cues_missing_column(self):
        """Test that normalize_cues raises error for missing column."""
        df = pd.DataFrame({'wrong_col': ['Hello']})
        with pytest.raises(ValueError):
            normalize_cues(df, cue_col='nonexistent')

class TestBuildInverseIndex:
    """Unit tests for inverse index building."""

    def test_index_structure(self):
        """Test that index maps normalized titles to candidates."""
        tracks = pd.DataFrame({
            'track_title': ['Hello World', 'Hello World', 'Test Song'],
            'artist_name': ['Artist A', 'Artist B', 'Artist C']
        })
        index = build_inverse_index(tracks)
        
        assert 'hello world' in index
        assert len(index['hello world']) == 2
        assert ('Hello World', 'Artist A') in index['hello world']
        assert ('Hello World', 'Artist B') in index['hello world']

    def test_missing_title_column(self):
        """Test error when title column is missing."""
        tracks = pd.DataFrame({'wrong_col': ['Hello']})
        with pytest.raises(ValueError):
            build_inverse_index(tracks, title_col='nonexistent')

class TestFuzzyMatching:
    """Unit tests for fuzzy matching logic (T020)."""

    def test_exact_match(self):
        """Test exact match returns distance 0."""
        cues = pd.DataFrame({'cue_text': ['Hello World']})
        tracks = pd.DataFrame({
            'track_title': ['Hello World'],
            'artist_name': ['Artist A']
        })
        
        matched, unmatched = match_cues(cues, tracks, max_levenshtein=4)
        
        assert len(matched) == 1
        assert len(unmatched) == 0
        assert matched.loc[0, 'levenshtein_distance'] == 0

    def test_within_threshold(self):
        """Test match within Levenshtein threshold."""
        cues = pd.DataFrame({'cue_text': ['Helo World']})  # 1 char diff
        tracks = pd.DataFrame({
            'track_title': ['Hello World'],
            'artist_name': ['Artist A']
        })
        
        matched, unmatched = match_cues(cues, tracks, max_levenshtein=4)
        
        assert len(matched) == 1
        assert matched.loc[0, 'levenshtein_distance'] == 1

    def test_outside_threshold(self):
        """Test no match when distance exceeds threshold."""
        cues = pd.DataFrame({'cue_text': ['Xyz']})
        tracks = pd.DataFrame({
            'track_title': ['Hello World'],
            'artist_name': ['Artist A']
        })
        
        matched, unmatched = match_cues(cues, tracks, max_levenshtein=1)
        
        assert len(matched) == 0
        assert len(unmatched) == 1

    def test_unmatched_logging(self, tmp_path):
        """Test that unmatched cues are logged to file."""
        cues = pd.DataFrame({'cue_text': ['NoMatch123']})
        tracks = pd.DataFrame({
            'track_title': ['Hello World'],
            'artist_name': ['Artist A']
        })
        output_path = tmp_path / "unmatched.csv"
        
        match_cues(cues, tracks, max_levenshtein=1, output_path=output_path)
        
        assert output_path.exists()
        unmatched_df = pd.read_csv(output_path)
        assert len(unmatched_df) == 1

class TestAggregation:
    """Unit tests for aggregation logic (T021)."""
    
    # Note: Aggregation logic is primarily tested in test_aggregation.py
    # These tests verify that match_cues produces data ready for aggregation
    
    def test_matched_data_structure(self):
        """Test that matched data has required columns for aggregation."""
        cues = pd.DataFrame({'cue_text': ['Hello'], 'user_id': ['U1']})
        tracks = pd.DataFrame({
            'track_title': ['Hello'],
            'artist_name': ['Artist A']
        })
        
        matched, _ = match_cues(cues, tracks)
        
        assert 'matched_track_title' in matched.columns
        assert 'matched_artist' in matched.columns
        assert 'levenshtein_distance' in matched.columns
        assert 'user_id' in matched.columns  # Preserved from original

class TestCollisionResolution:
    """Unit tests for collision resolution."""

    def test_resolve_collisions_returns_dataframe(self):
        """Test that resolve_collisions returns a DataFrame."""
        matched = pd.DataFrame({
            'cue_text': ['Test'],
            'matched_track_title': ['Test Song'],
            'matched_artist': ['Artist A'],
            'levenshtein_distance': [0]
        })
        
        result = resolve_collisions(matched)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1

    def test_resolve_collisions_preserves_data(self):
        """Test that resolve_collisions preserves input data."""
        matched = pd.DataFrame({
            'cue_text': ['Test'],
            'matched_track_title': ['Test Song'],
            'matched_artist': ['Artist A'],
            'levenshtein_distance': [0]
        })
        
        result = resolve_collisions(matched)
        
        assert result.loc[0, 'cue_text'] == 'Test'
        assert result.loc[0, 'matched_track_title'] == 'Test Song'