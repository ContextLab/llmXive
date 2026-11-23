"""
Unit tests for the lexicon module.
"""

import pytest
import tempfile
import os
from pathlib import Path
import csv

from src.bias_pipeline.lexicon import load_lexicon, match_lexicon
from src.bias_pipeline.utils import PipelineError


class TestLoadLexicon:
    def test_load_from_csv(self):
        """Test loading lexicon from a valid CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "lexicon.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['term', 'category'])
                writer.writeheader()
                writer.writerow({'term': 'admin', 'category': 'role'})
                writer.writerow({'term': 'user', 'category': 'role'})
                writer.writerow({'term': 'blacklist', 'category': 'bias'})
            
            lexicon = load_lexicon(csv_path)
            
            assert 'admin' in lexicon
            assert 'user' in lexicon
            assert 'blacklist' in lexicon
            assert len(lexicon) == 3

    def test_load_empty_csv(self):
        """Test loading an empty lexicon CSV."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "lexicon.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['term', 'category'])
                writer.writeheader()
            
            lexicon = load_lexicon(csv_path)
            assert len(lexicon) == 0

    def test_load_missing_file(self):
        """Test that loading a non-existent file raises PipelineError."""
        with pytest.raises(PipelineError):
            load_lexicon(Path("/non/existent/path/lexicon.csv"))

    def test_load_csv_missing_column(self):
        """Test that loading a CSV without the required column raises PipelineError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "lexicon.csv"
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['word', 'category']) # 'word' is valid, but let's test wrong one
                writer.writeheader()
                writer.writerow({'word': 'admin', 'category': 'role'})
            
            # This should work because 'word' is a valid column name
            # Let's test a truly invalid column
            csv_path2 = Path(tmpdir) / "lexicon2.csv"
            with open(csv_path2, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['foo', 'bar'])
                writer.writeheader()
                writer.writerow({'foo': 'admin', 'bar': 'role'})
            
            with pytest.raises(PipelineError):
                load_lexicon(csv_path2)

class TestMatchLexicon:
    def test_match_basic(self):
        """Test basic matching functionality."""
        lexicon = {'admin', 'user', 'blacklist'}
        tokens = ['Admin', 'User', 'guest', 'BLACKLIST']
        
        result = match_lexicon(tokens, lexicon)
        
        assert result['match_count'] == 3
        assert 'admin' in result['matches']
        assert 'user' in result['matches']
        assert 'blacklist' in result['matches']
        assert result['match_ratio'] == 3.0 / 4.0

    def test_match_empty_tokens(self):
        """Test matching with empty token list."""
        lexicon = {'admin', 'user'}
        tokens = []
        
        result = match_lexicon(tokens, lexicon)
        
        assert result['matches'] == []
        assert result['match_count'] == 0
        assert result['match_ratio'] == 0.0

    def test_match_no_matches(self):
        """Test matching when no tokens match."""
        lexicon = {'admin', 'user'}
        tokens = ['guest', 'developer']
        
        result = match_lexicon(tokens, lexicon)
        
        assert result['matches'] == []
        assert result['match_count'] == 0
        assert result['match_ratio'] == 0.0

    def test_case_insensitivity(self):
        """Test that matching is case-insensitive."""
        lexicon = {'Admin'}
        tokens = ['admin', 'ADMIN', 'AdMiN']
        
        result = match_lexicon(tokens, lexicon)
        
        assert result['match_count'] == 3