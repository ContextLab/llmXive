"""
Unit tests for data filtering logic (User Story 2).

This module tests the filtering criteria defined for the "Subtle Cue" dataset
(high-frequency transients, low-amplitude events) and the "Control Set".

It verifies that:
1. The filtering logic correctly identifies subtle vs. control classes.
2. The class mapping from names to IDs is consistent.
3. The filtering function works on a mock dataset structure.
"""

import pytest
from typing import List, Dict, Any
from unittest.mock import MagicMock, patch

# We are testing logic that will be used by code/data/subtle_cue_builder.py
# and code/data/loader.py. Since those are not fully implemented yet (T020/T021),
# we define the expected logic here to ensure the implementation matches the spec.
# The actual implementation in subtle_cue_builder.py must match these expectations.

# --- Mock Data & Helpers ---

# Expected Subtle Cue Classes (Spec: freq > 8kHz OR amplitude < -40dBFS)
# Examples: "glass breaking", "alarm", "whisper"
EXPECTED_SUBTLE_CLASSES = {
    "glass_breaking",
    "alarm",
    "whisper",
    "siren",
    "high_pitch_squeal"
}

# Expected Control Set Classes (Spec: low-frequency, high-amplitude)
# Examples: "engine_hum", "heavy_traffic" (from UrbanSound8K mapping)
EXPECTED_CONTROL_CLASSES = {
    "engine_hum",
    "heavy_traffic",
    "air_conditioner",
    "drilling",
    "jackhammer"
}

# Mock dataset sample structure
MOCK_DATASET_SAMPLE = [
    {"audio": {"path": "dummy.wav"}, "label_name": "glass_breaking", "label_id": 0},
    {"audio": {"path": "dummy.wav"}, "label_name": "engine_hum", "label_id": 1},
    {"audio": {"path": "dummy.wav"}, "label_name": "whisper", "label_id": 2},
    {"audio": {"path": "dummy.wav"}, "label_name": "bird_chirp", "label_id": 3}, # Neutral
    {"audio": {"path": "dummy.wav"}, "label_name": "siren", "label_id": 4},
    {"audio": {"path": "dummy.wav"}, "label_name": "jackhammer", "label_id": 5},
]

def mock_filter_subtle_cues(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mock implementation of the filtering logic to be tested.
    In the real implementation (code/data/subtle_cue_builder.py), this will
    apply the actual frequency/amplitude thresholds or class name mapping.
    """
    return [
        item for item in dataset
        if item["label_name"] in EXPECTED_SUBTLE_CLASSES
    ]

def mock_filter_control_set(dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mock implementation of the control set filtering logic.
    """
    return [
        item for item in dataset
        if item["label_name"] in EXPECTED_CONTROL_CLASSES
    ]

def mock_get_class_mapping() -> Dict[str, int]:
    """
    Mock implementation of class name to ID mapping.
    """
    return {
        "glass_breaking": 0,
        "engine_hum": 1,
        "whisper": 2,
        "bird_chirp": 3,
        "siren": 4,
        "jackhammer": 5,
    }

# --- Tests ---

class TestSubtleCueFiltering:
    """Tests for the Subtle Cue filtering logic (T021)."""

    def test_filter_subtle_cues_returns_correct_items(self):
        """Verify that subtle cues are correctly identified."""
        filtered = mock_filter_subtle_cues(MOCK_DATASET_SAMPLE)
        names = {item["label_name"] for item in filtered}
        
        assert names == EXPECTED_SUBTLE_CLASSES, f"Expected {EXPECTED_SUBTLE_CLASSES}, got {names}"
        assert len(filtered) == 3, "Should have 3 subtle items in mock data"

    def test_filter_subtle_cues_excludes_control_and_neutral(self):
        """Verify that control and neutral items are excluded."""
        filtered = mock_filter_subtle_cues(MOCK_DATASET_SAMPLE)
        names = {item["label_name"] for item in filtered}
        
        assert "engine_hum" not in names, "Control set should be excluded"
        assert "jackhammer" not in names, "Control set should be excluded"
        assert "bird_chirp" not in names, "Neutral class should be excluded"

    def test_filter_subtle_cues_empty_dataset(self):
        """Verify behavior on empty dataset."""
        filtered = mock_filter_subtle_cues([])
        assert filtered == []

    def test_filter_subtle_cues_no_matches(self):
        """Verify behavior when no subtle cues exist."""
        dataset = [
            {"label_name": "engine_hum", "label_id": 1},
            {"label_name": "bird_chirp", "label_id": 3},
        ]
        filtered = mock_filter_subtle_cues(dataset)
        assert filtered == []


class TestControlSetFiltering:
    """Tests for the Control Set filtering logic (T021b)."""

    def test_filter_control_set_returns_correct_items(self):
        """Verify that control set items are correctly identified."""
        filtered = mock_filter_control_set(MOCK_DATASET_SAMPLE)
        names = {item["label_name"] for item in filtered}
        
        assert names == EXPECTED_CONTROL_CLASSES, f"Expected {EXPECTED_CONTROL_CLASSES}, got {names}"
        assert len(filtered) == 2, "Should have 2 control items in mock data"

    def test_filter_control_set_excludes_subtle_and_neutral(self):
        """Verify that subtle and neutral items are excluded."""
        filtered = mock_filter_control_set(MOCK_DATASET_SAMPLE)
        names = {item["label_name"] for item in filtered}
        
        assert "glass_breaking" not in names, "Subtle set should be excluded"
        assert "whisper" not in names, "Subtle set should be excluded"
        assert "bird_chirp" not in names, "Neutral class should be excluded"

    def test_filter_control_set_empty_dataset(self):
        """Verify behavior on empty dataset."""
        filtered = mock_filter_control_set([])
        assert filtered == []


class TestClassMapping:
    """Tests for class name to ID mapping logic."""

    def test_mapping_contains_expected_classes(self):
        """Verify that the mapping includes all expected subtle and control classes."""
        mapping = mock_get_class_mapping()
        
        for cls in EXPECTED_SUBTLE_CLASSES | EXPECTED_CONTROL_CLASSES:
            assert cls in mapping, f"Class {cls} missing from mapping"

    def test_mapping_values_are_unique(self):
        """Verify that IDs are unique."""
        mapping = mock_get_class_mapping()
        ids = list(mapping.values())
        assert len(ids) == len(set(ids)), "Mapping IDs must be unique"

    def test_mapping_format(self):
        """Verify mapping is a dict of str -> int."""
        mapping = mock_get_class_mapping()
        assert isinstance(mapping, dict)
        for k, v in mapping.items():
            assert isinstance(k, str)
            assert isinstance(v, int)


class TestIntegrationFiltering:
    """Integration tests for the combined filtering logic."""

    def test_mutual_exclusivity(self):
        """Verify that a class cannot be both subtle and control."""
        intersection = EXPECTED_SUBTLE_CLASSES & EXPECTED_CONTROL_CLASSES
        assert len(intersection) == 0, "Subtle and Control sets must be disjoint"

    def test_filtering_consistency(self):
        """Verify that filtering is consistent across multiple runs."""
        dataset = MOCK_DATASET_SAMPLE * 10  # Repeat to ensure consistency
        
        filtered_subtle = mock_filter_subtle_cues(dataset)
        filtered_control = mock_filter_control_set(dataset)
        
        # Check counts
        assert len(filtered_subtle) == len(EXPECTED_SUBTLE_CLASSES) * 10
        assert len(filtered_control) == len(EXPECTED_CONTROL_CLASSES) * 10

        # Check no overlap in results
        subtle_names = {item["label_name"] for item in filtered_subtle}
        control_names = {item["label_name"] for item in filtered_control}
        assert subtle_names.isdisjoint(control_names)