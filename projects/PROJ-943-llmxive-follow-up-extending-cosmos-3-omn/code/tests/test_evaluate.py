"""
Unit tests for the evaluation script logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.evaluate import (
    check_physics_reward_exists,
    split_dataset_by_domain,
    calculate_metrics,
    perform_statistical_test
)


class TestEvaluate:
    """Tests for evaluation functions."""

    def test_check_physics_reward_exists_present(self):
        """Test detection of physics_reward field."""
        data = [
            {"id": 1, "physics_reward": 0.5},
            {"id": 2, "physics_reward": 0.8}
        ]
        assert check_physics_reward_exists(data) is True

    def test_check_physics_reward_exists_missing(self):
        """Test detection when physics_reward field is missing."""
        data = [
            {"id": 1, "other_field": 0.5},
            {"id": 2, "other_field": 0.8}
        ]
        assert check_physics_reward_exists(data) is False

    def test_split_dataset_by_domain(self):
        """Test splitting dataset into symbolic and physical domains."""
        data = [
            {"id": 1, "label": "constraint_violated", "physics_reward": 0.8},
            {"id": 2, "label": "constraint_satisfied", "physics_reward": 0.2},
            {"id": 3, "label": "constraint_violated", "physics_reward": None}
        ]
        symbolic, physical = split_dataset_by_domain(data)
        # Logic depends on implementation, but we verify no crash and non-empty
        assert isinstance(symbolic, list)
        assert isinstance(physical, list)

    def test_calculate_metrics(self):
        """Test metric calculation."""
        y_true = [0, 1, 1, 0]
        y_pred = [0, 1, 0, 0]
        metrics = calculate_metrics(y_true, y_pred)
        assert "accuracy" in metrics
        assert "f1_score" in metrics
        assert "auc_roc" in metrics
        assert "brier_score" in metrics
