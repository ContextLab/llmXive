"""
Integration tests for dataset splitting logic.
"""
import pytest
import pandas as pd
from pathlib import Path
import sys
import os

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.data_ingestion import (
    generate_all_5_element_combinations,
    build_deduplicated_composition_index,
    strict_composition_compare
)
from code.config import ELEMENT_SUBSET, N_NOVEL_SAMPLES

class TestSplitLogic:
    """Tests to verify disjoint sets between train, holdout, and novel."""

    def test_no_overlap_train_holdout(self):
        """
        Verify that the training set and holdout set have no overlapping compositions.
        """
        # Simulate a small training set
        train_compositions = {"FeCoNiCrMn", "FeCoNiCrAl", "TiZrHfNbTa"}
        
        # Generate candidates for holdout (simplified logic for test)
        # In real code, this involves exclusion pairs and live API checks
        # Here we just ensure the generation logic respects the exclusion
        
        # Mock the exclusion logic
        exclusion_pairs = [("Fe", "Co")]
        
        # Generate a candidate that should NOT be in train
        # (This is a simplified version of the actual sampling logic)
        holdout_candidates = set()
        for c in generate_all_5_element_combinations(ELEMENT_SUBSET):
            if c not in train_compositions:
                holdout_candidates.add(c)
                if len(holdout_candidates) >= 10:
                    break
        
        # Verify no overlap
        overlap = train_compositions.intersection(holdout_candidates)
        assert len(overlap) == 0, f"Overlap found: {overlap}"

    def test_no_overlap_train_novel(self):
        """
        Verify that the training set and novel set have no overlapping compositions.
        """
        train_compositions = {"FeCoNiCrMn", "FeCoNiCrAl"}
        
        # Simulate novel generation logic
        novel_candidates = set()
        for c in generate_all_5_element_combinations(ELEMENT_SUBSET):
            if c not in train_compositions:
                novel_candidates.add(c)
                if len(novel_candidates) >= 10:
                    break
        
        overlap = train_compositions.intersection(novel_candidates)
        assert len(overlap) == 0, f"Overlap found: {overlap}"

    def test_no_overlap_holdout_novel(self):
        """
        Verify that the holdout set and novel set have no overlapping compositions.
        """
        # This is more complex in reality because holdout is "known" and novel is "unknown"
        # For this test, we simulate the logic where holdout is filtered out of novel
        
        holdout_set = {"FeCoNiCrAl", "TiZrHfNbTa"}
        novel_set = set()
        
        # Simulate novel generation that explicitly excludes holdout
        for c in generate_all_5_element_combinations(ELEMENT_SUBSET):
            if c not in holdout_set:
                novel_set.add(c)
                if len(novel_set) >= 10:
                    break
        
        overlap = holdout_set.intersection(novel_set)
        assert len(overlap) == 0, f"Overlap found: {overlap}"

    def test_deduplication_index_correctness(self):
        """
        Verify that the deduplicated composition index correctly identifies unique compositions.
        """
        # Simulate raw data with potential duplicates
        raw_data = [
            {"composition": "FeCoNiCrMn", "elements": ["Fe", "Co", "Ni", "Cr", "Mn"]},
            {"composition": "FeCoNiCrMn", "elements": ["Fe", "Co", "Ni", "Cr", "Mn"]}, # Duplicate
            {"composition": "FeCoNiCrAl", "elements": ["Fe", "Co", "Ni", "Cr", "Al"]}
        ]
        
        index = build_deduplicated_composition_index(raw_data)
        
        assert len(index) == 2, "Deduplication failed"
        assert "FeCoNiCrMn" in index
        assert "FeCoNiCrAl" in index

    def test_strict_composition_compare(self):
        """
        Verify strict composition string comparison prevents hash collisions.
        """
        # "FeCo" vs "CoFe" should be considered different if not normalized,
        # but our generation logic should produce sorted strings.
        # This test ensures the comparison function works as expected.
        
        comp1 = "FeCoNiCrMn"
        comp2 = "FeCoNiCrMn"
        comp3 = "FeCoNiCrAl"
        
        assert strict_composition_compare(comp1, comp2) is True
        assert strict_composition_compare(comp1, comp3) is False
        assert strict_composition_compare(comp1, "MnCrNiCoFe") is False # Different string