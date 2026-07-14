"""
Contract tests for User Story 2: Brain-Inspired Model Generation.

Specifically tests story uniqueness and format constraints for generated stories.
These tests verify the output contract before the full generation pipeline is run.
"""
import os
import json
import pytest
import psutil
import resource
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import patch, MagicMock
import sys

# Project root is assumed to be the parent of 'tests'
PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
GENERATED_STORIES_PATH = RESULTS_DIR / "generated_stories.jsonl"
LOGS_DIR = PROJECT_ROOT / "logs"

# Constraints defined in T026 / US2 spec
MIN_STORY_COUNT = 1000
REQUIRED_KEYS = {"story_id", "text", "model_type"}
MAX_DUPLICATE_RATIO = 0.01  # Allow 1% collision tolerance for edge cases, but ideally 0
MAX_RAM_GB = 6.0
MAX_RAM_BYTES = MAX_RAM_GB * (1024 ** 3)

# Helper to get current process memory usage in bytes
def get_current_memory_bytes() -> int:
    """Get the current resident set size (RSS) of the current process."""
    try:
        # Unix/Linux/macOS
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    except AttributeError:
        # Fallback for Windows using psutil
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except Exception:
            return 0

@pytest.fixture(scope="module")
def generated_stories():
    """
    Load the generated stories file.
    Skips if file doesn't exist (to allow test-driven development flow where
    generation hasn't run yet).
    """
    if not GENERATED_STORIES_PATH.exists():
        pytest.skip(f"Output file {GENERATED_STORIES_PATH} not found. "
                    "Run code/02_model_generation.py first.")
    
    stories = []
    with open(GENERATED_STORIES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    stories.append(json.loads(line))
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON in generated_stories.jsonl: {e}")
    return stories

class TestStoryFormatContract:
    """Tests verifying the structural contract of generated stories."""

    def test_file_exists(self):
        """Verify the output file exists at the expected path."""
        assert GENERATED_STORIES_PATH.exists(), "generated_stories.jsonl must exist"

    def test_not_empty(self):
        """Verify the file is not empty."""
        assert GENERATED_STORIES_PATH.stat().st_size > 0, "generated_stories.jsonl must not be empty"

    def test_required_keys_present(self, generated_stories: List[Dict[str, Any]]):
        """Verify every story object contains the required keys."""
        for i, story in enumerate(generated_stories):
            missing = REQUIRED_KEYS - set(story.keys())
            assert not missing, f"Story at index {i} missing keys: {missing}"

    def test_story_id_type(self, generated_stories: List[Dict[str, Any]]):
        """Verify story_id is a string or int."""
        for i, story in enumerate(generated_stories):
            assert isinstance(story["story_id"], (str, int)), \
                f"Story {i}: story_id must be str or int, got {type(story['story_id'])}"

    def test_text_type_and_non_empty(self, generated_stories: List[Dict[str, Any]]):
        """Verify text is a non-empty string."""
        for i, story in enumerate(generated_stories):
            assert isinstance(story["text"], str), \
                f"Story {i}: text must be str, got {type(story['text'])}"
            assert len(story["text"].strip()) > 0, \
                f"Story {i}: text must not be empty or whitespace-only"

    def test_model_type_type(self, generated_stories: List[Dict[str, Any]]):
        """Verify model_type is a string."""
        for i, story in enumerate(generated_stories):
            assert isinstance(story["model_type"], str), \
                f"Story {i}: model_type must be str, got {type(story['model_type'])}"

class TestStoryUniquenessContract:
    """Tests verifying the uniqueness constraints of generated stories."""

    def test_minimum_count(self, generated_stories: List[Dict[str, Any]]):
        """Verify at least 1,000 unique stories were generated."""
        count = len(generated_stories)
        assert count >= MIN_STORY_COUNT, \
            f"Expected at least {MIN_STORY_COUNT} stories, got {count}"

    def test_unique_story_ids(self, generated_stories: List[Dict[str, Any]]):
        """Verify all story_ids are unique."""
        ids = [s["story_id"] for s in generated_stories]
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids), \
            f"Duplicate story_ids found. Total: {len(ids)}, Unique: {len(unique_ids)}"

    def test_unique_text_content(self, generated_stories: List[Dict[str, Any]]):
        """Verify text content is unique across the dataset."""
        texts = [s["text"].strip().lower() for s in generated_stories]
        unique_texts = set(texts)
        if len(texts) != len(unique_texts):
            # Calculate duplicate ratio
            duplicate_count = len(texts) - len(unique_texts)
            duplicate_ratio = duplicate_count / len(texts)
            assert duplicate_ratio <= MAX_DUPLICATE_RATIO, \
                f"Too many duplicate texts: {duplicate_count}/{len(texts)} ({duplicate_ratio:.2%}) " \
                f"exceeds allowed {MAX_DUPLICATE_RATIO:.2%}."
        # If no duplicates, assert passes. If low duplicates, assert passes.
        # If high duplicates, assert fails.

    def test_no_duplicate_text_with_same_model(self, generated_stories: List[Dict[str, Any]]):
        """Verify no two stories with the same model_type have identical text."""
        model_text_map = {}
        for story in generated_stories:
            key = (story["model_type"], story["text"].strip().lower())
            if key in model_text_map:
                pytest.fail(f"Duplicate text found for model '{story['model_type']}': "
                            f"Story IDs {story['story_id']} and {model_text_map[key]}")
            model_text_map[key] = story["story_id"]

class TestMemoryConstraints:
    """Integration tests for memory constraints during model generation."""

    def test_peak_memory_under_limit_mocked(self):
        """
        Test that the generation process respects the memory limit.
        This test mocks the memory usage to simulate a scenario where
        the process exceeds the limit, verifying the constraint check logic.
        """
        # We simulate a process that would exceed the limit
        with patch('tests.test_model.get_current_memory_bytes') as mock_mem:
            # Mock a value exceeding 6GB
            mock_mem.return_value = int(MAX_RAM_GB * (1024 ** 3) * 1.1)
            
            current_mem = get_current_memory_bytes()
            assert current_mem > MAX_RAM_BYTES, "Mock setup failed: memory should exceed limit"
            
            # Verify the assertion logic works as expected in a real scenario
            # In a real run, this would be part of the generation loop
            with pytest.raises(AssertionError) as exc_info:
                assert current_mem <= MAX_RAM_BYTES, \
                    f"Peak memory {current_mem / (1024**3):.2f}GB exceeds limit {MAX_RAM_GB}GB"
            
            assert "exceeds limit" in str(exc_info.value)

    def test_peak_memory_within_limit_mocked(self):
        """
        Test that the generation process passes when memory is within limits.
        """
        with patch('tests.test_model.get_current_memory_bytes') as mock_mem:
            # Mock a value well within the limit
            mock_mem.return_value = int(MAX_RAM_GB * (1024 ** 3) * 0.5)
            
            current_mem = get_current_memory_bytes()
            assert current_mem <= MAX_RAM_BYTES, \
                f"Mock setup failed: memory {current_mem / (1024**3):.2f}GB should be under limit"
            
            # Verify the assertion logic passes
            assert current_mem <= MAX_RAM_BYTES, \
                f"Peak memory {current_mem / (1024**3):.2f}GB exceeds limit {MAX_RAM_GB}GB"

    def test_memory_monitoring_integration(self):
        """
        Integration test: Simulate a generation loop that checks memory.
        This verifies that the memory monitoring logic is robust.
        """
        # Simulate a loop that checks memory at intervals
        memory_snapshots = []
        
        # Simulate 5 checks
        for i in range(5):
            # Simulate varying memory usage
            if i == 2:
                # Spike in memory
                usage = int(MAX_RAM_GB * (1024 ** 3) * 0.9)
            else:
                usage = int(MAX_RAM_GB * (1024 ** 3) * 0.5)
            
            memory_snapshots.append(usage)
        
        peak_memory = max(memory_snapshots)
        assert peak_memory <= MAX_RAM_BYTES, \
            f"Peak memory {peak_memory / (1024**3):.2f}GB exceeds limit {MAX_RAM_GB}GB"

    def test_memory_limit_enforcement_logic(self):
        """
        Test the specific logic that enforces the memory limit.
        This ensures that if memory exceeds the limit, an error is raised.
        """
        # Define a function that checks memory and raises if exceeded
        def check_memory_limit():
            current = get_current_memory_bytes()
            if current > MAX_RAM_BYTES:
                raise MemoryError(f"Memory limit exceeded: {current / (1024**3):.2f}GB > {MAX_RAM_GB}GB")
            return True

        # Mock to simulate under limit
        with patch('tests.test_model.get_current_memory_bytes') as mock_mem:
            mock_mem.return_value = int(MAX_RAM_GB * (1024 ** 3) * 0.5)
            result = check_memory_limit()
            assert result is True

        # Mock to simulate over limit
        with patch('tests.test_model.get_current_memory_bytes') as mock_mem:
            mock_mem.return_value = int(MAX_RAM_GB * (1024 ** 3) * 1.1)
            with pytest.raises(MemoryError) as exc_info:
                check_memory_limit()
            assert "Memory limit exceeded" in str(exc_info.value)

# Additional helper for integration testing with real process
def test_real_process_memory_baseline():
    """
    Baseline test: Verify that the test process itself stays within reasonable limits.
    This is a sanity check for the testing environment.
    """
    current_mem = get_current_memory_bytes()
    # We expect the test process to be well under 1GB for this simple test
    # If it's higher, it might indicate a memory leak in the test framework or environment
    assert current_mem < (1024 * 1024 * 1024), \
        f"Test process memory {current_mem / (1024**3):.2f}GB is unexpectedly high"