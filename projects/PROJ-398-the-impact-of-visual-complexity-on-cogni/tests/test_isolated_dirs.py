"""
Test suite for T018a: Verify isolated test data directories exist.

This test ensures that the `tests/data/` directory structure required for
isolated testing (specifically for contract tests like T018) is present.
"""
import os
import pytest
from pathlib import Path


TEST_DATA_DIR = Path(__file__).parent / "data"


class TestIsolatedDirs:
    """Tests for verifying the existence of isolated test data directories."""

    def test_directories_exist(self):
        """
        Verify that the isolated test data directory `tests/data/` exists.
        
        This test asserts that the directory required for T018a (Setup isolated
        test data directories) has been created.
        """
        assert TEST_DATA_DIR.exists(), f"Directory {TEST_DATA_DIR} does not exist."
        assert TEST_DATA_DIR.is_dir(), f"{TEST_DATA_DIR} is not a directory."

    def test_blank_background_fixture_exists(self):
        """
        Verify that the blank background test fixture exists.
        
        This ensures the data required for T018 (Contract test: blank background edge case)
        is available.
        """
        blank_bg = TEST_DATA_DIR / "blank_background.png"
        assert blank_bg.exists(), f"Fixture {blank_bg} does not exist."
        assert blank_bg.is_file(), f"{blank_bg} is not a file."

    def test_high_entropy_fixture_exists(self):
        """
        Verify that the high entropy noise test fixture exists.
        
        Used for testing metric extraction on complex backgrounds.
        """
        high_entropy = TEST_DATA_DIR / "high_entropy_noise.png"
        assert high_entropy.exists(), f"Fixture {high_entropy} does not exist."
        assert high_entropy.is_file(), f"{high_entropy} is not a file."

    def test_low_entropy_fixture_exists(self):
        """
        Verify that the low entropy solid test fixture exists.
        
        Used for testing metric extraction on simple backgrounds.
        """
        low_entropy = TEST_DATA_DIR / "low_entropy_solid.png"
        assert low_entropy.exists(), f"Fixture {low_entropy} does not exist."
        assert low_entropy.is_file(), f"{low_entropy} is not a file."