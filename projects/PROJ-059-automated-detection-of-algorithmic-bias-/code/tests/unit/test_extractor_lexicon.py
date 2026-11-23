import pytest
from pathlib import Path
import tempfile
import csv
import os
import sys

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.bias_pipeline.extractor import match_lexicon, normalize_tokens
from src.bias_pipeline.lexicon import load_lexicon


class TestMatchLexicon:
    """Unit tests for the match_lexicon function (T015)."""

    def test_empty_inputs(self):
        """Test with empty tokens or lexicon."""
        assert match_lexicon([], set()) == (0, [])
        assert match_lexicon(['token'], set()) == (0, [])
        assert match_lexicon([], {'token'}) == (0, [])

    def test_exact_match(self):
        """Test exact matching of tokens."""
        tokens = ['user', 'admin', 'black', 'white']
        lexicon = {'black', 'white', 'asian'}
        
        count, matches = match_lexicon(tokens, lexicon)
        assert count == 2
        assert set(matches) == {'black', 'white'}

    def test_case_insensitive(self):
        """Test that normalization handles case."""
        # normalize_tokens should handle this before match_lexicon
        tokens = normalize_tokens("BlackUser and WhiteAdmin")
        # Expected normalized: ['black', 'user', 'and', 'white', 'admin']
        lexicon = {'black', 'white'}
        
        count, matches = match_lexicon(tokens, lexicon)
        assert count == 2
        assert 'black' in matches
        assert 'white' in matches

    def test_no_match(self):
        """Test when no tokens match the lexicon."""
        tokens = ['variable', 'function', 'loop']
        lexicon = {'demographic', 'race', 'gender'}
        
        count, matches = match_lexicon(tokens, lexicon)
        assert count == 0
        assert matches == []

    def test_duplicate_tokens(self):
        """Test that duplicate tokens are counted once per unique match."""
        tokens = ['black', 'black', 'white', 'white', 'white']
        lexicon = {'black', 'white'}
        
        # match_lexicon uses set intersection, so duplicates in input list 
        # are collapsed.
        count, matches = match_lexicon(tokens, lexicon)
        assert count == 2 # Only unique matches
        assert set(matches) == {'black', 'white'}

    def test_integration_with_normalize(self):
        """Test full pipeline: normalize then match."""
        raw_text = "CamelCaseVariable and snake_case_var"
        normalized = normalize_tokens(raw_text)
        
        # Assume 'camel' and 'snake' are in lexicon for this test
        lexicon = {'camel', 'snake', 'case'}
        
        count, matches = match_lexicon(normalized, lexicon)
        # 'camel', 'case', 'snake', 'var' -> 'camel', 'case', 'snake' match
        assert count >= 2 # At least camel and snake

    def test_lexicon_loading_integration(self):
        """Test match_lexicon with a real CSV-loaded lexicon."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.writer(f)
            writer.writerow(['term', 'category'])
            writer.writerow(['race', 'demographic'])
            writer.writerow(['gender', 'demographic'])
            writer.writerow(['age', 'demographic'])
            temp_path = f.name

        try:
            lexicon = load_lexicon(temp_path)
            tokens = ['race', 'gender', 'variable', 'age']
            
            count, matches = match_lexicon(tokens, lexicon)
            assert count == 3
            assert set(matches) == {'race', 'gender', 'age'}
        finally:
            os.unlink(temp_path)
