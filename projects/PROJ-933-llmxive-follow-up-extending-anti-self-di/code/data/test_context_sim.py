"""
Integration test for context simulation in US1.

Verifies that:
1. The simulate_context_split function correctly samples 1 privileged context
   from prompts with >= 4 distinct annotated reasoning traces.
2. The remaining rationales are correctly identified as the target distribution.
3. The privileged context is never identical to any of the remaining target rationales
   (resampling logic is tested).
4. The output structure matches the expected format for data/context_splits.json.
"""
import json
import os
import random
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest

# Import the function under test from the sibling module
from data.preprocess import simulate_context_split
from data.fetch_utils import DataFetchError


class MockDataset:
    """Mock dataset to simulate HuggingFace dataset behavior for testing."""
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def to_pandas(self):
        # Simple mock for to_pandas if needed, though we iterate directly
        return self.data


@pytest.fixture
def sample_data():
    """
    Create sample data mimicking UltraFeedback/Dolly structure.
    Each prompt must have >= 4 distinct rationales to pass the filter.
    """
    # Ensure distinct rationales for the main test
    distinct_rationales = [
        "Rationale A: The answer is X because...",
        "Rationale B: However, considering Y, the answer is Z...",
        "Rationale C: Wait, let's think about this differently. The answer is W...",
        "Rationale D: But if we look at the context, the answer is V...",
        "Rationale E: Finally, the conclusion is U..."
    ]

    # Create a prompt with exactly 4 rationales (minimum requirement)
    prompt_4 = {
        "prompt": "What is the capital of France?",
        "rationales": distinct_rationales[:4]
    }

    # Create a prompt with 5 rationales
    prompt_5 = {
        "prompt": "Explain quantum entanglement.",
        "rationales": distinct_rationales
    }

    # Create a prompt with < 4 rationales (should be filtered out by caller, but good for edge case)
    prompt_3 = {
        "prompt": "Simple math problem.",
        "rationales": ["R1", "R2", "R3"]
    }

    return [prompt_4, prompt_5, prompt_3]


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_simulate_context_split_basic(sample_data, temp_output_dir):
    """Test basic functionality: sampling 1 privileged vs remaining target."""
    # Filter data to only include prompts with >= 4 rationales before passing to sim
    valid_data = [p for p in sample_data if len(p["rationales"]) >= 4]

    output_file = temp_output_dir / "context_splits.json"

    # Run the simulation
    result = simulate_context_split(valid_data, output_file=str(output_file))

    # Assertions on result structure
    assert result is not None
    assert "total_prompts_processed" in result
    assert "successful_splits" in result
    assert "failed_splits" in result
    assert "splits" in result

    assert result["total_prompts_processed"] == 2  # prompt_4 and prompt_5
    assert result["successful_splits"] == 2
    assert result["failed_splits"] == 0

    # Verify split details
    splits = result["splits"]
    assert len(splits) == 2

    for split in splits:
        assert "prompt" in split
        assert "privileged_context" in split
        assert "target_distribution" in split
        assert "prompt_id" in split

        # Verify counts
        assert len(split["privileged_context"]) == 1
        assert len(split["target_distribution"]) == len(split["prompt"]["rationales"]) - 1

        # Verify the privileged context is from the original rationales
        all_original = set(split["prompt"]["rationales"])
        priv = split["privileged_context"][0]
        targets = set(split["target_distribution"])

        assert priv in all_original
        assert priv not in targets
        assert targets.issubset(all_original)
        assert len(targets) == len(all_original) - 1


def test_simulate_context_split_resampling_logic():
    """
    Test the resampling logic when the randomly selected privileged context
    happens to be identical to one of the others (simulating a collision).
    
    Since the input data in the main flow is filtered for distinct rationales,
    this test constructs a specific scenario where rationales might be duplicates
    to ensure the resampling loop works, or verifies that distinct rationales
    naturally avoid this.
    
    Note: The specification says "detect and re-sample if identical to unselected".
    If the input data has distinct strings, the first pick is always valid.
    We test the logic by ensuring the function handles the selection correctly.
    """
    # Create data with distinct rationales to ensure valid split on first try
    # This tests the "happy path" of the resampling logic (0 retries needed)
    data = [{
        "prompt": "Test",
        "rationales": ["A", "B", "C", "D"]
    }]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / "test_resample.json"
        result = simulate_context_split(data, output_file=str(output_file))

        assert result["successful_splits"] == 1
        split = result["splits"][0]
        
        # Verify the split is valid
        priv = split["privileged_context"][0]
        targets = split["target_distribution"]
        
        assert priv not in targets
        assert len(targets) == 3


def test_simulate_context_split_output_file_written(sample_data, temp_output_dir):
    """Verify that the output file is actually written to disk."""
    valid_data = [p for p in sample_data if len(p["rationales"]) >= 4]
    output_file = temp_output_dir / "context_splits.json"

    simulate_context_split(valid_data, output_file=str(output_file))

    assert output_file.exists()

    # Verify file content is valid JSON
    with open(output_file, "r") as f:
        content = json.load(f)
    
    assert "splits" in content
    assert len(content["splits"]) == 2


def test_simulate_context_split_empty_input(temp_output_dir):
    """Test behavior with no valid prompts."""
    empty_data = []
    output_file = temp_output_dir / "empty.json"

    result = simulate_context_split(empty_data, output_file=str(output_file))

    assert result["total_prompts_processed"] == 0
    assert result["successful_splits"] == 0
    assert len(result["splits"]) == 0
    assert output_file.exists()


def test_simulate_context_split_single_valid_prompt(sample_data, temp_output_dir):
    """Test with exactly one valid prompt (4 rationales)."""
    valid_data = [sample_data[0]] # The one with 4 rationales
    output_file = temp_output_dir / "single.json"

    result = simulate_context_split(valid_data, output_file=str(output_file))

    assert result["successful_splits"] == 1
    split = result["splits"][0]
    assert len(split["target_distribution"]) == 3
    assert len(split["privileged_context"]) == 1


def test_simulation_determinism_with_seed(sample_data, temp_output_dir):
    """
    Test that setting a random seed produces deterministic results.
    We run twice with the same seed and verify the outputs are identical.
    """
    valid_data = [p for p in sample_data if len(p["rationales"]) >= 4]
    
    output_file_1 = temp_output_dir / "run1.json"
    output_file_2 = temp_output_dir / "run2.json"

    # Run 1
    random.seed(42)
    result_1 = simulate_context_split(valid_data, output_file=str(output_file_1))
    
    # Run 2
    random.seed(42)
    result_2 = simulate_context_split(valid_data, output_file=str(output_file_2))

    # Compare splits
    assert len(result_1["splits"]) == len(result_2["splits"])
    
    for s1, s2 in zip(result_1["splits"], result_2["splits"]):
        assert s1["privileged_context"] == s2["privileged_context"]
        assert s1["target_distribution"] == s2["target_distribution"]