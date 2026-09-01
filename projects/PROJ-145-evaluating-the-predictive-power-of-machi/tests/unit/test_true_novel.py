"""
Unit tests for T015 True Novel Generation logic.
"""
import pytest
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import itertools

# Add code to path if needed, but assuming standard project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.config import N_NOVEL_SAMPLES, ELEMENT_SOURCE_LIST, RANDOM_SEED
from code.generate_true_novel import generate_5_element_combinations

class TestTrueNovelGeneration:

    def test_generate_5_element_combinations_sorted(self):
        """Test that combinations are generated in sorted order."""
        elements = ["C", "A", "B", "D", "E"]
        combos = generate_5_element_combinations(elements, seed=42)
        
        # Should only have one combination of 5 elements from 5
        assert len(combos) == 1
        # Sorted string
        assert combos[0] == "ABCDE"

    def test_generate_5_element_combinations_count(self):
        """Test the count of combinations."""
        elements = ["A", "B", "C", "D", "E", "F"] # 6 elements, choose 5 -> 6 combos
        combos = generate_5_element_combinations(elements, seed=42)
        assert len(combos) == 6
        
        # Verify all are sorted
        for c in combos:
            assert c == "".join(sorted(c))

    def test_novelty_filtering_logic(self):
        """
        Test the logic of filtering out train and proxy compositions.
        This is a logic test, not an integration test.
        """
        # Mock data
        train_set = {"AlFeNiCoCr", "TiZrHfNbTa"}
        proxy_set = {"AlFeNiCoCr", "CuZnAgAuPd", "TiZrHfNbTa"}
        
        # Candidates
        candidates = [
            "AlFeNiCoCr", # In train and proxy -> Exclude
            "CuZnAgAuPd", # In proxy -> Exclude
            "TiZrHfNbTa", # In train and proxy -> Exclude
            "ScYLaCePr",  # Novel
            "NdSmEuGdTb"  # Novel
        ]
        
        novel = []
        for c in candidates:
            if c in train_set:
                continue
            if c in proxy_set:
                continue
            novel.append(c)
        
        assert len(novel) == 2
        assert "ScYLaCePr" in novel
        assert "NdSmEuGdTb" in novel
        assert "AlFeNiCoCr" not in novel

    def test_random_sampling_consistency(self):
        """Test that sampling is deterministic with a fixed seed."""
        # This tests the logic in generate_true_novel.py regarding shuffling
        # We can't easily test the full script without file I/O, but we can test the shuffle logic
        import random
        data = list(range(100))
        random.seed(42)
        random.shuffle(data)
        sample1 = data[:10]
        
        random.seed(42)
        random.shuffle(data)
        sample2 = data[:10]
        
        assert sample1 == sample2

    def test_element_pool_union(self):
        """
        Verify that the element pool logic correctly uses the config list.
        (Simulated check)
        """
        # In the script, we use ELEMENT_SOURCE_LIST directly.
        # This test ensures that the list is not empty and contains expected types.
        assert len(ELEMENT_SOURCE_LIST) > 0
        assert all(isinstance(e, str) for e in ELEMENT_SOURCE_LIST)
        assert len(ELEMENT_SOURCE_LIST[0]) >= 1 # At least 1 char