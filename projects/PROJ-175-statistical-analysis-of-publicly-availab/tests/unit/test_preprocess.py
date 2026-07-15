import pytest
import pandas as pd
import numpy as np
import json
import os
import sys
from pathlib import Path
from Levenshtein import distance as levenshtein_distance

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.preprocess import normalize_ingredient_name, build_canonical_map, LEVENSHTEIN_THRESHOLD

class TestNormalizeIngredient:
    def test_lowercase_and_strip(self):
        assert normalize_ingredient_name("  Apple  ") == "apple"
    
    def test_remove_descriptors(self):
        assert normalize_ingredient_name("Fresh Apple") == "apple"
        assert normalize_ingredient_name("Dried Apple") == "apple"
        assert normalize_ingredient_name("Chopped Apple") == "apple"
        assert normalize_ingredient_name("Extra Virgin Olive Oil") == "olive oil"
    
    def test_remove_punctuation(self):
        assert normalize_ingredient_name("Apple, fresh") == "apple fresh"
        assert normalize_ingredient_name("Onion (white)") == "onion white"
    
    def test_non_string(self):
        assert normalize_ingredient_name(123) == "123"
        assert normalize_ingredient_name(None) == ""

class TestLevenshteinMapping:
    def test_exact_match(self):
        # Setup
        recipe_df = pd.DataFrame({'ingredient_name': ['Apple']})
        flavordb_df = pd.DataFrame({
            'canonical_name': ['Apple'],
            'id': ['ID_001']
        })
        
        mapping = build_canonical_map(recipe_df, flavordb_df)
        assert mapping['Apple'] == 'ID_001'
    
    def test_close_match_threshold_2(self):
        # "Apples" vs "Apple" -> distance 1
        recipe_df = pd.DataFrame({'ingredient_name': ['Apples']})
        flavordb_df = pd.DataFrame({
            'canonical_name': ['Apple'],
            'id': ['ID_002']
        })
        
        mapping = build_canonical_map(recipe_df, flavordb_df)
        # Should match because distance( "apples", "apple" ) = 1 <= 2
        assert mapping['Apples'] == 'ID_002'
    
    def test_no_match_above_threshold(self):
        # "Banana" vs "Apple" -> distance 4 (b-a-n-a-n-a vs a-p-p-l-e)
        # Actually: b-a-n-a-n-a (6) vs a-p-p-l-e (5)
        # d = 4? b!=a, a!=p, n!=p, a!=l, n!=e, a (del) -> 5?
        # Let's use a clear non-match
        recipe_df = pd.DataFrame({'ingredient_name': ['Banana']})
        flavordb_df = pd.DataFrame({
            'canonical_name': ['Apple'],
            'id': ['ID_003']
        })
        
        mapping = build_canonical_map(recipe_df, flavordb_df)
        # Distance between "banana" and "apple" is > 2
        assert mapping['Banana'] == 'Unknown'
    
    def test_threshold_boundary(self):
        # "Cat" vs "Cut" -> distance 1
        # "Cat" vs "Cart" -> distance 1
        # "Cat" vs "Catch" -> distance 2
        # "Cat" vs "Cater" -> distance 2 (c-a-t vs c-a-t-e-r -> 2 inserts)
        # "Cat" vs "Caterpillar" -> > 2
        
        recipe_df = pd.DataFrame({'ingredient_name': ['Cater']})
        flavordb_df = pd.DataFrame({
            'canonical_name': ['Cat'],
            'id': ['ID_004']
        })
        
        mapping = build_canonical_map(recipe_df, flavordb_df)
        # "cater" vs "cat" -> 2 edits (e, r) -> 2 <= 2 -> Match
        assert mapping['Cater'] == 'ID_004'

class TestIntegrationPreprocess:
    def test_map_generation_structure(self, tmp_path):
        # Create dummy data
        recipe_df = pd.DataFrame({
            'recipe_id': [1, 1, 2],
            'ingredient_name': ['Apple', 'Banana', 'Cherry']
        })
        flavordb_df = pd.DataFrame({
            'canonical_name': ['Apple', 'Cherry'],
            'id': ['A', 'C']
        })
        
        # Build map
        mapping = build_canonical_map(recipe_df, flavordb_df)
        
        assert 'Apple' in mapping
        assert 'Cherry' in mapping
        assert 'Banana' in mapping
        assert mapping['Banana'] == 'Unknown'
        assert mapping['Apple'] == 'A'
        assert mapping['Cherry'] == 'C'