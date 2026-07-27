"""
Tests for the preprocessing module.
"""
import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data.preprocess import (
    levenshtein_similarity,
    normalize_ingredient_name,
    build_canonical_map,
    process_chunk_normalize
)

class TestLevenshteinSimilarity:
    def test_exact_match(self):
        assert levenshtein_similarity("flour", "flour") == 0
        assert levenshtein_similarity("sugar", "sugar") == 0
        
    def test_one_character_difference(self):
        assert levenshtein_similarity("flour", "flou") == 1
        assert levenshtein_similarity("flour", "flours") == 1
        assert levenshtein_similarity("flour", "plour") == 1
        
    def test_two_character_difference(self):
        assert levenshtein_similarity("flour", "flou") == 1
        assert levenshtein_similarity("flour", "flours") == 1
        assert levenshtein_similarity("flour", "plour") == 1
        assert levenshtein_similarity("flour", "plou") == 2
        assert levenshtein_similarity("flour", "plours") == 2
        
    def test_large_difference(self):
        assert levenshtein_similarity("flour", "xyz") == 3
        assert levenshtein_similarity("flour", "abcdef") == 6

class TestNormalizeIngredientName:
    def setup_method(self):
        self.canonical_map = {
            "flour": "flour",
            "sugar": "sugar",
            "salt": "salt",
            "butter": "butter",
            "egg": "egg"
        }
        
    def test_exact_match(self):
        result, is_mapped = normalize_ingredient_name("flour", self.canonical_map)
        assert result == "flour"
        assert is_mapped == True
        
    def test_case_insensitive(self):
        result, is_mapped = normalize_ingredient_name("FLOUR", self.canonical_map)
        assert result == "flour"
        assert is_mapped == True
        
    def test_one_character_difference(self):
        result, is_mapped = normalize_ingredient_name("flou", self.canonical_map)
        assert result == "flour"
        assert is_mapped == True
        
    def test_two_character_difference(self):
        result, is_mapped = normalize_ingredient_name("plou", self.canonical_map)
        assert result == "flour"
        assert is_mapped == True
        
    def test_three_character_difference(self):
        result, is_mapped = normalize_ingredient_name("plourr", self.canonical_map)
        assert result != "flour"
        assert is_mapped == False
        
    def test_empty_string(self):
        result, is_mapped = normalize_ingredient_name("", self.canonical_map)
        assert result == ""
        assert is_mapped == False
        
    def test_none_input(self):
        result, is_mapped = normalize_ingredient_name(None, self.canonical_map)
        assert result is None
        assert is_mapped == False

class TestBuildCanonicalMap:
    def test_build_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            raw_data_path = Path(tmpdir) / "raw_data.parquet"
            # Create a dummy file
            raw_data_path.touch()
            
            canonical_map = build_canonical_map(str(raw_data_path))
            
            assert isinstance(canonical_map, dict)
            assert len(canonical_map) > 0
            assert "flour" in canonical_map
            
            # Check that the canonical map file was created
            canonical_path = Path(tmpdir) / "canonical_map.json"
            assert canonical_path.exists()
            
            # Verify the content
            with open(canonical_path, 'r') as f:
                saved_map = json.load(f)
            assert saved_map == canonical_map

class TestProcessChunkNormalize:
    def test_process_chunk(self):
        # Create a sample chunk
        chunk = pd.DataFrame({
            'ingredient': ['flour', 'sugar', 'salt', 'flou', 'plou']
        })
        
        canonical_map = {
            "flour": "flour",
            "sugar": "sugar",
            "salt": "salt"
        }
        
        result, mapped_count, excluded_count = process_chunk_normalize(chunk, canonical_map)
        
        assert 'normalized_ingredient' in result.columns
        assert 'is_mapped' in result.columns
        assert result['normalized_ingredient'].iloc[0] == "flour"
        assert result['is_mapped'].iloc[0] == True
        assert result['is_mapped'].iloc[3] == True  # "flou" -> "flour"
        assert result['is_mapped'].iloc[4] == True  # "plou" -> "flour" (distance 2)
        
        assert mapped_count == 5
        assert excluded_count == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])