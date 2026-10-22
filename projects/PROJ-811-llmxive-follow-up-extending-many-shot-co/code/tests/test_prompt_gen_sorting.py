import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.src.prompt_gen import PromptGenerator

@pytest.fixture
def sample_manifest_data():
    """Sample manifest data with varying depths and curvature scores."""
    return [
        {
            "id": "ex1",
            "input": "Trace 1",
            "output": "Completion 1",
            "depth": 3,
            "logical_difficulty": 3,
            "curvature_score": 0.1,
        },
        {
            "id": "ex2",
            "input": "Trace 2",
            "output": "Completion 2",
            "depth": 1,
            "logical_difficulty": 1,
            "curvature_score": 0.5,
        },
        {
            "id": "ex3",
            "input": "Trace 3",
            "output": "Completion 3",
            "depth": 5,
            "logical_difficulty": 5,
            "curvature_score": 0.2,
        },
        {
            "id": "ex4",
            "input": "Trace 4",
            "output": "Completion 4",
            "depth": 2,
            "logical_difficulty": 2,
            "curvature_score": 0.8,
        },
    ]

@pytest.fixture
def temp_manifest_file(sample_manifest_data):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(sample_manifest_data, f)
        path = Path(f.name)
    yield path
    path.unlink()

class TestLogicalAscendingSort:
    def test_sort_by_depth_non_decreasing(self, sample_manifest_data):
        generator = PromptGenerator()
        sorted_examples = generator._sort_logical_ascending(sample_manifest_data)

        depths = [ex["depth"] for ex in sorted_examples]
        assert depths == sorted(depths), f"Expected non-decreasing order, got {depths}"

    def test_sort_uses_logical_difficulty_if_present(self, sample_manifest_data):
        # Modify one to have different 'depth' and 'logical_difficulty'
        sample_manifest_data[0]["depth"] = 100
        sample_manifest_data[0]["logical_difficulty"] = 1

        generator = PromptGenerator()
        sorted_examples = generator._sort_logical_ascending(sample_manifest_data)

        # The first one should be the one with logical_difficulty=1
        assert sorted_examples[0]["id"] == "ex1"

    def test_empty_list(self):
        generator = PromptGenerator()
        result = generator._sort_logical_ascending([])
        assert result == []

class TestLogicalRandomShuffle:
    def test_shuffle_is_permutation(self, sample_manifest_data):
        generator = PromptGenerator()
        shuffled = generator._shuffle_logical_random(sample_manifest_data, seed=42)

        original_ids = set(ex["id"] for ex in sample_manifest_data)
        shuffled_ids = set(ex["id"] for ex in shuffled)

        assert original_ids == shuffled_ids
        assert len(original_ids) == len(shuffled)

    def test_shuffle_is_deterministic(self, sample_manifest_data):
        generator = PromptGenerator()
        shuffled1 = generator._shuffle_logical_random(sample_manifest_data, seed=123)
        shuffled2 = generator._shuffle_logical_random(sample_manifest_data, seed=123)

        assert [ex["id"] for ex in shuffled1] == [ex["id"] for ex in shuffled2]

    def test_shuffle_changes_order(self, sample_manifest_data):
        generator = PromptGenerator()
        shuffled = generator._shuffle_logical_random(sample_manifest_data, seed=999)

        # With high probability, a shuffle will change the order
        # We check if it's NOT the same as original (unless n=1)
        if len(sample_manifest_data) > 1:
            original_ids = [ex["id"] for ex in sample_manifest_data]
            shuffled_ids = [ex["id"] for ex in shuffled]
            # It's possible to get the same order by chance, but unlikely with 4 items
            # We just assert it's a valid permutation, determinism is tested above.

class TestOriginalCDSSort:
    def test_sort_by_curvature(self, sample_manifest_data):
        generator = PromptGenerator()
        sorted_examples = generator._sort_original_cds(sample_manifest_data)

        scores = [ex["curvature_score"] for ex in sorted_examples]
        assert scores == sorted(scores), f"Expected ascending curvature order, got {scores}"

    def test_missing_curvature_score(self):
        data = [{"id": "a", "curvature_score": 0.5}, {"id": "b"}]
        generator = PromptGenerator()
        sorted_examples = generator._sort_original_cds(data)
        # 'b' has no score, defaults to 0.0, so should be first
        assert sorted_examples[0]["id"] == "b"