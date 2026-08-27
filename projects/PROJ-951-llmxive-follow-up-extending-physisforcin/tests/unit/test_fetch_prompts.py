import os
import json
import pytest
from pathlib import Path

# Determine the project root based on the task's directory structure
# The test runs from within the 'code' directory or we assume standard layout
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROMPTS_FILE = DATA_DIR / "prompts.jsonl"

class TestFetchPrompts:
    """
    Unit tests for T053: fetch_robotbench_prompts.
    Verifies that data/prompts.jsonl exists and contains at least 10 entries.
    """

    def test_prompts_file_exists(self):
        """Asserts that the prompts.jsonl file exists in the data directory."""
        assert PROMPTS_FILE.exists(), f"Expected {PROMPTS_FILE} to exist. " \
                                      "Run T053 (src/prompts/fetch_robotbench_prompts.py) first."

    def test_prompts_file_not_empty(self):
        """Asserts that the prompts file is not empty."""
        assert PROMPTS_FILE.stat().st_size > 0, f"{PROMPTS_FILE} is empty."

    def test_minimum_entry_count(self):
        """
        Asserts that the prompts file contains at least 10 valid entries.
        Reads the file line-by-line (JSONL format) to count entries.
        """
        count = 0
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    json.loads(line)
                    count += 1
                except json.JSONDecodeError as e:
                    pytest.fail(f"Invalid JSON on line {count + 1}: {e}")

        assert count >= 10, (
            f"Expected at least 10 entries in {PROMPTS_FILE}, "
            f"but found {count}. "
            "Ensure T053 successfully downloaded a real dataset from RobotBench."
        )

    def test_entry_structure(self):
        """
        Optional: Verify that entries have a 'prompt' or 'text' key.
        This ensures the data is usable for generation tasks.
        """
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Check for common prompt keys used in generation
                    assert 'prompt' in entry or 'text' in entry, (
                        f"Entry {i} missing 'prompt' or 'text' key: {entry}"
                    )
                    break  # Only check the first valid entry to avoid noise
                except json.JSONDecodeError:
                    continue  # Skip invalid lines if any (though test_minimum_entry_count catches this)