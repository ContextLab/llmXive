"""
Unit tests for T033b: save_complexity_scores.py

Tests verify:
1. Correct CSV output format (pr_id, complexity_score)
2. Proper handling of empty diffs
3. Integration with complexity module
"""
import csv
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from code.analysis.save_complexity_scores import (
    extract_pr_diff,
    calculate_complexity_score,
    save_complexity_scores,
)

class TestExtractPrDiff:
    """Tests for extract_pr_diff function."""
    
    def test_extract_from_direct_diff_field(self):
        """Should extract diff from top-level 'diff' field."""
        pr = {
            'pr_id': 123,
            'diff': 'def foo():\n    pass'
        }
        result = extract_pr_diff(pr)
        assert result == 'def foo():\n    pass'
    
    def test_extract_from_nested_raw_diff(self):
        """Should extract diff from raw.diff when top-level is missing."""
        pr = {
            'pr_id': 123,
            'raw': {
                'diff': 'class Bar:\n    def method(self): pass'
            }
        }
        result = extract_pr_diff(pr)
        assert result == 'class Bar:\n    def method(self): pass'
    
    def test_extract_from_patch_fallback(self):
        """Should use 'patch' field as fallback."""
        pr = {
            'pr_id': 123,
            'patch': 'diff --git a/file.py b/file.py\n+print("hello")'
        }
        result = extract_pr_diff(pr)
        assert result == 'diff --git a/file.py b/file.py\n+print("hello")'
    
    def test_empty_when_no_diff_available(self):
        """Should return empty string when no diff fields present."""
        pr = {
            'pr_id': 123,
            'title': 'Fix bug'
        }
        result = extract_pr_diff(pr)
        assert result == ''
    
    def test_handles_none_values(self):
        """Should handle None values gracefully."""
        pr = {
            'pr_id': 123,
            'diff': None,
            'raw': None
        }
        result = extract_pr_diff(pr)
        assert result == ''

class TestCalculateComplexityScore:
    """Tests for calculate_complexity_score function."""
    
    @patch('code.analysis.save_complexity_scores.analyze_diff_complexity')
    def test_returns_complexity_from_module(self, mock_analyze):
        """Should return complexity score from analyze_diff_complexity."""
        mock_analyze.return_value = 5.0
        diff = 'def foo():\n    if True:\n        pass'
        result = calculate_complexity_score(diff)
        assert result == 5.0
        mock_analyze.assert_called_once_with(diff)
    
    @patch('code.analysis.save_complexity_scores.analyze_diff_complexity')
    def test_handles_none_return(self, mock_analyze):
        """Should return 0.0 when module returns None."""
        mock_analyze.return_value = None
        diff = 'some code'
        result = calculate_complexity_score(diff)
        assert result == 0.0
    
    @patch('code.analysis.save_complexity_scores.analyze_diff_complexity')
    def test_handles_exceptions_gracefully(self, mock_analyze):
        """Should return 0.0 when module raises exception."""
        mock_analyze.side_effect = Exception("Parse error")
        diff = 'invalid code {{{{'
        result = calculate_complexity_score(diff)
        assert result == 0.0
    
    def test_empty_diff_returns_zero(self):
        """Should return 0.0 for empty diff."""
        result = calculate_complexity_score('')
        assert result == 0.0
    
    def test_whitespace_only_diff_returns_zero(self):
        """Should return 0.0 for whitespace-only diff."""
        result = calculate_complexity_score('   \n\t  ')
        assert result == 0.0
    
    def test_clamps_negative_to_zero(self):
        """Should clamp negative complexity to 0.0."""
        with patch('code.analysis.save_complexity_scores.analyze_diff_complexity') as mock_analyze:
            mock_analyze.return_value = -5.0
            result = calculate_complexity_score('code')
            assert result == 0.0

class TestSaveComplexityScores:
    """Tests for save_complexity_scores function."""
    
    def test_writes_correct_csv_format(self, tmp_path):
        """Should write CSV with pr_id and complexity_score columns."""
        prs = [
            {'pr_id': 1, 'diff': 'def foo(): pass'},
            {'pr_id': 2, 'diff': 'def bar():\n    if True:\n        pass'},
        ]
        output_path = tmp_path / 'complexity_scores.csv'
        
        with patch('code.analysis.save_complexity_scores.analyze_diff_complexity') as mock_analyze:
            mock_analyze.side_effect = [1.0, 3.0]
            save_complexity_scores(prs, output_path)
        
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert 'pr_id' in rows[0]
        assert 'complexity_score' in rows[0]
    
    def test_handles_string_pr_ids(self, tmp_path):
        """Should convert string pr_ids to integers."""
        prs = [
            {'pr_id': '123', 'diff': 'code'},
            {'pr_id': '456', 'diff': 'code'},
        ]
        output_path = tmp_path / 'complexity_scores.csv'
        
        with patch('code.analysis.save_complexity_scores.analyze_diff_complexity') as mock_analyze:
            mock_analyze.return_value = 1.0
            save_complexity_scores(prs, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert rows[0]['pr_id'] == '123'
        assert rows[1]['pr_id'] == '456'
    
    def test_skips_invalid_pr_ids(self, tmp_path):
        """Should skip rows with invalid pr_ids."""
        prs = [
            {'pr_id': 'invalid', 'diff': 'code'},
            {'pr_id': 456, 'diff': 'code'},
        ]
        output_path = tmp_path / 'complexity_scores.csv'
        
        with patch('code.analysis.save_complexity_scores.analyze_diff_complexity') as mock_analyze:
            mock_analyze.return_value = 1.0
            save_complexity_scores(prs, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Only the valid row should be written
        assert len(rows) == 1
        assert rows[0]['pr_id'] == '456'
    
    def test_creates_output_directory(self, tmp_path):
        """Should create parent directory if it doesn't exist."""
        prs = [{'pr_id': 1, 'diff': 'code'}]
        output_path = tmp_path / 'subdir' / 'complexity_scores.csv'
        
        with patch('code.analysis.save_complexity_scores.analyze_diff_complexity') as mock_analyze:
            mock_analyze.return_value = 1.0
            save_complexity_scores(prs, output_path)
        
        assert output_path.parent.exists()
        assert output_path.exists()