"""
Unit tests for prompt template generation in code/inference/prompts.py.

Tests verify that:
1. All three prompt templates (Monolithic, Separated, Generic) are generated correctly.
2. Placeholders are correctly substituted with provided arguments.
3. Missing arguments raise appropriate errors (or handle gracefully).
4. Edge cases (empty strings, None values) are handled as expected.
"""
import pytest
from unittest.mock import patch
from typing import Dict, Any, Optional

# Import the functions to test based on the API surface
from inference.prompts import (
    get_monolithic_prompt,
    get_separated_tracks_prompt,
    get_generic_baseline_prompt,
    build_prompt
)

# Test fixtures
@pytest.fixture
def sample_profile_data() -> Dict[str, Any]:
    return {
        "domain": "coding",
        "capability_rules": "Must write unit tests first.",
        "behavior_keywords": ["efficient", "clean", "documented"]
    }

@pytest.fixture
def sample_task_data() -> Dict[str, Any]:
    return {
        "id": "task_001",
        "description": "Implement a binary search tree.",
        "domain": "coding"
    }

class TestPromptGeneration:
    """Test suite for prompt generation functions."""

    def test_monolithic_prompt_format(self, sample_profile_data, sample_task_data):
        """Test that Monolithic prompt follows the expected format."""
        prompt = get_monolithic_prompt(
            domain_expert=sample_profile_data["domain"],
            behavior_keywords=" ".join(sample_profile_data["behavior_keywords"]),
            task=sample_task_data["description"]
        )
        
        expected_prefix = "[System: You are coding who efficient clean documented. Task: Implement a binary search tree.]"
        assert prompt.startswith("[System:")
        assert "You are coding" in prompt
        assert "who efficient clean documented" in prompt
        assert "Task: Implement a binary search tree." in prompt
        assert prompt.endswith("]")

    def test_separated_tracks_prompt_format(self, sample_profile_data, sample_task_data):
        """Test that Separated Tracks prompt correctly splits capability and behavior."""
        prompt = get_separated_tracks_prompt(
            capability_rules=sample_profile_data["capability_rules"],
            behavior_keywords=" ".join(sample_profile_data["behavior_keywords"]),
            task=sample_task_data["description"]
        )
        
        assert prompt.startswith("[System: Capability:")
        assert "Capability: Must write unit tests first." in prompt
        assert "Behavior: efficient clean documented" in prompt
        assert "Task: Implement a binary search tree." in prompt
        assert prompt.endswith("]")

    def test_generic_baseline_prompt_format(self, sample_task_data):
        """Test that Generic Baseline prompt uses the standard helpful assistant template."""
        prompt = get_generic_baseline_prompt(
            task=sample_task_data["description"]
        )
        
        expected = "[System: You are a helpful assistant. Task: Implement a binary search tree.]"
        assert prompt == expected

    def test_build_prompt_dispatch_monolithic(self, sample_profile_data, sample_task_data):
        """Test build_prompt correctly routes to Monolithic template."""
        prompt = build_prompt(
            condition="monolithic",
            domain_expert=sample_profile_data["domain"],
            behavior_keywords=" ".join(sample_profile_data["behavior_keywords"]),
            task=sample_task_data["description"]
        )
        
        assert "You are coding" in prompt
        assert "who efficient clean documented" in prompt

    def test_build_prompt_dispatch_separated(self, sample_profile_data, sample_task_data):
        """Test build_prompt correctly routes to Separated Tracks template."""
        prompt = build_prompt(
            condition="separated",
            capability_rules=sample_profile_data["capability_rules"],
            behavior_keywords=" ".join(sample_profile_data["behavior_keywords"]),
            task=sample_task_data["description"]
        )
        
        assert "Capability: Must write unit tests first." in prompt
        assert "Behavior: efficient clean documented" in prompt

    def test_build_prompt_dispatch_generic(self, sample_task_data):
        """Test build_prompt correctly routes to Generic Baseline template."""
        prompt = build_prompt(
            condition="generic",
            task=sample_task_data["description"]
        )
        
        assert "You are a helpful assistant" in prompt

    def test_build_prompt_invalid_condition(self, sample_task_data):
        """Test that build_prompt raises ValueError for invalid condition."""
        with pytest.raises(ValueError, match="Invalid condition"):
            build_prompt(
                condition="invalid_condition",
                task=sample_task_data["description"]
            )

    def test_empty_task_description(self):
        """Test handling of empty task description."""
        prompt = get_monolithic_prompt(
            domain_expert="coding",
            behavior_keywords="clean",
            task=""
        )
        assert "Task: " in prompt
        assert prompt.endswith("]")

    def test_special_characters_in_task(self):
        """Test handling of special characters in task description."""
        task = "Solve: 2 + 2 = ? (Answer: 4)"
        prompt = get_generic_baseline_prompt(task=task)
        assert task in prompt

    def test_long_behavior_keywords(self):
        """Test handling of a large list of behavior keywords."""
        keywords = ["keyword" + str(i) for i in range(50)]
        prompt = get_separated_tracks_prompt(
            capability_rules="Rule A",
            behavior_keywords=" ".join(keywords),
            task="Simple task"
        )
        
        for kw in keywords:
            assert kw in prompt

    def test_whitespace_handling(self):
        """Test that extra whitespace in inputs is preserved or handled predictably."""
        # Inputs with extra spaces
        prompt = get_monolithic_prompt(
            domain_expert="  math  ",
            behavior_keywords="  clean  ",
            task="  task  "
        )
        # The prompt should contain the inputs exactly as provided (or trimmed if logic dictates)
        # Assuming the implementation uses them directly:
        assert "  math  " in prompt or "math" in prompt # Check presence
        assert "  task  " in prompt or "task" in prompt

    def test_none_values_handling(self):
        """Test that None values are handled (either by raising or defaulting)."""
        # Depending on implementation, this might raise TypeError or handle gracefully.
        # We expect the function to not crash silently with wrong types if typed properly.
        # If the implementation expects strings, passing None might raise.
        # Let's test the generic baseline which only needs task.
        with pytest.raises((TypeError, AttributeError)):
            get_generic_baseline_prompt(task=None)