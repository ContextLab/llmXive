"""
Unit tests for T017: Missing Thinking Prefix Filtering

Tests the filtering logic for removing records with missing 'thinking' prefixes.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.lib.data_filtering import filter_missing_thinking, load_filtered_dataset, save_filtered_dataset

class TestT017Filtering:
    """Test cases for T017 filtering logic."""
    
    def test_filter_missing_thinking_valid_records(self):
        """Test filtering with all valid records (no skips)."""
        dataset = [
            {'problem_id': 'p1', 'thinking': 'I need to calculate...', 'data': 1},
            {'problem_id': 'p2', 'thinking': 'Let me think about...', 'data': 2},
        ]
        
        filtered, skipped = filter_missing_thinking(dataset)
        
        assert len(filtered) == 2
        assert skipped == 0
        assert filtered[0]['problem_id'] == 'p1'
        assert filtered[1]['problem_id'] == 'p2'
    
    def test_filter_missing_thinking_with_null_thinking(self):
        """Test filtering with None thinking values."""
        dataset = [
            {'problem_id': 'p1', 'thinking': 'Valid thinking', 'data': 1},
            {'problem_id': 'p2', 'thinking': None, 'data': 2},
            {'problem_id': 'p3', 'thinking': 'Also valid', 'data': 3},
        ]
        
        filtered, skipped = filter_missing_thinking(dataset)
        
        assert len(filtered) == 2
        assert skipped == 1
        assert filtered[0]['problem_id'] == 'p1'
        assert filtered[1]['problem_id'] == 'p3'
    
    def test_filter_missing_thinking_with_empty_string(self):
        """Test filtering with empty string thinking values."""
        dataset = [
            {'problem_id': 'p1', 'thinking': 'Valid thinking', 'data': 1},
            {'problem_id': 'p2', 'thinking': '', 'data': 2},
            {'problem_id': 'p3', 'thinking': '   ', 'data': 3},  # whitespace only
            {'problem_id': 'p4', 'thinking': 'Valid again', 'data': 4},
        ]
        
        filtered, skipped = filter_missing_thinking(dataset)
        
        assert len(filtered) == 2
        assert skipped == 2
        assert filtered[0]['problem_id'] == 'p1'
        assert filtered[1]['problem_id'] == 'p4'
    
    def test_filter_missing_thinking_all_invalid(self):
        """Test filtering when all records have missing thinking."""
        dataset = [
            {'problem_id': 'p1', 'thinking': None, 'data': 1},
            {'problem_id': 'p2', 'thinking': '', 'data': 2},
        ]
        
        filtered, skipped = filter_missing_thinking(dataset)
        
        assert len(filtered) == 0
        assert skipped == 2
    
    def test_filter_missing_thinking_mixed_whitespace(self):
        """Test filtering with various whitespace-only thinking values."""
        dataset = [
            {'problem_id': 'p1', 'thinking': 'Valid', 'data': 1},
            {'problem_id': 'p2', 'thinking': '  \\t\\n  ', 'data': 2},  # whitespace
            {'problem_id': 'p3', 'thinking': 'Also valid', 'data': 3},
        ]
        
        filtered, skipped = filter_missing_thinking(dataset)
        
        assert len(filtered) == 2
        assert skipped == 1
    
    def test_save_and_load_filtered_dataset(self):
        """Test saving and loading a filtered dataset."""
        dataset = [
            {'problem_id': 'p1', 'thinking': 'Valid', 'data': 1},
            {'problem_id': 'p2', 'thinking': None, 'data': 2},  # Should be filtered
        ]
        
        filtered, _ = filter_missing_thinking(dataset)
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "test_filtered.json"
            save_filtered_dataset(filtered, path)
            
            loaded = load_filtered_dataset(path)
            
            assert len(loaded) == 1
            assert loaded[0]['problem_id'] == 'p1'
    
    def test_filter_with_missing_problem_id(self):
        """Test filtering when problem_id is missing (uses index)."""
        dataset = [
            {'thinking': 'Valid', 'data': 1},
            {'thinking': None, 'data': 2},  # Should be filtered
        ]
        
        filtered, skipped = filter_missing_thinking(dataset)
        
        assert len(filtered) == 1
        assert skipped == 1
        # The record should still be present, just with a generated problem_id
        assert 'problem_id' in filtered[0] or filtered[0].get('problem_id') is not None