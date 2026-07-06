"""
Tests for code/02_randomization.py

Verifies:
1. Unique Participant ID generation
2. Balanced distribution (50/50 split) over multiple runs
3. Correct JSON output structure
"""
import pytest
import json
import os
import sys
import random
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.utils.random_utils import set_global_seed
from code.utils.logger import setup_logger
from code import code_02_randomization as randomization_module


class TestParticipantIdGeneration:
    """Test that participant IDs are unique and properly formatted."""

    def test_generate_unique_ids(self):
        """Ensure that generated IDs are unique across multiple calls."""
        ids = set()
        for _ in range(100):
            pid = randomization_module.generate_participant_id()
            assert pid not in ids, f"Duplicate ID generated: {pid}"
            ids.add(pid)
            # Check format (8 chars, uppercase alphanumeric)
            assert len(pid) == 8
            assert pid.isupper()
            assert pid.isalnum()


class TestConditionAssignment:
    """Test the logic of condition assignment."""

    def test_assign_condition_valid_values(self):
        """Ensure assigned conditions are always 'Partner' or 'Tool'."""
        rng = random.Random(42)
        for _ in range(100):
            pid = randomization_module.generate_participant_id()
            condition = randomization_module.assign_condition(pid, rng)
            assert condition in ["Partner", "Tool"]

    def test_assign_condition_balanced_with_seed(self):
        """Test that a specific seed produces a known balanced distribution."""
        # Use a seed that we know produces a specific outcome for deterministic testing
        set_global_seed(12345)
        rng = random.Random()
        rng.seed(random.getstate()[1])

        counts = {"Partner": 0, "Tool": 0}
        for _ in range(1000):
            pid = randomization_module.generate_participant_id()
            cond = randomization_module.assign_condition(pid, rng)
            counts[cond] += 1

        # Check that both conditions are represented
        assert counts["Partner"] > 0
        assert counts["Tool"] > 0
        # Check approximate balance (within 5% for large N)
        total = sum(counts.values())
        assert 0.45 <= counts["Partner"] / total <= 0.55


class TestBalanceValidation:
    """Test the validation logic for balanced randomization."""

    def test_validate_balance_perfect(self):
        """Test validation with a perfectly balanced dataset."""
        assignments = [
            {"condition": "Partner"},
            {"condition": "Tool"},
            {"condition": "Partner"},
            {"condition": "Tool"}
        ]
        result = randomization_module.validate_balance(assignments)
        assert result["total"] == 4
        assert result["counts"]["Partner"] == 2
        assert result["counts"]["Tool"] == 2
        assert result["proportions"]["Partner"] == 0.5
        assert result["is_balanced"] is True

    def test_validate_balance_unbalanced(self):
        """Test validation with an unbalanced dataset."""
        # Create a dataset with 90% Partner
        assignments = [{"condition": "Partner"}] * 90 + [{"condition": "Tool"}] * 10
        result = randomization_module.validate_balance(assignments)
        assert result["total"] == 100
        assert result["is_balanced"] is False  # 90% is outside 50% +/- 10%

    def test_validate_balance_empty(self):
        """Test validation with an empty list."""
        result = randomization_module.validate_balance([])
        assert result["total"] == 0
        assert result["is_balanced"] is False


class TestRunRandomization:
    """Test the main randomization execution flow."""

    def test_run_randomization_count(self):
        """Verify that the correct number of assignments are generated."""
        n = 50
        assignments = randomization_module.run_randomization(n, seed=42)
        assert len(assignments) == n

    def test_run_randomization_structure(self):
        """Verify the structure of each assignment record."""
        assignments = randomization_module.run_randomization(5, seed=42)
        for item in assignments:
            assert "participant_id" in item
            assert "condition" in item
            assert "timestamp" in item
            assert "assignment_index" in item
            assert item["condition"] in ["Partner", "Tool"]
            assert isinstance(item["assignment_index"], int)


class TestSaveRandomizationLog:
    """Test the file saving functionality."""

    def test_save_creates_file(self, tmp_path):
        """Verify that the log file is created with correct content."""
        output_path = tmp_path / "test_log.json"
        assignments = [
            {"participant_id": "A1B2C3D4", "condition": "Partner", "timestamp": "2023-01-01", "assignment_index": 1}
        ]

        randomization_module.save_randomization_log(assignments, output_path)

        assert output_path.exists()
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert "metadata" in data
        assert "assignments" in data
        assert len(data["assignments"]) == 1
        assert data["assignments"][0]["participant_id"] == "A1B2C3D4"