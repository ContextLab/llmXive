"""
Unit tests for forgetting_metrics module (T026).
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from src.analysis.forgetting_metrics import (
    load_test_instances,
    load_agent_state,
    evaluate_agent_on_instances,
    calculate_accuracy_drop,
    calculate_retention_rate,
    compute_forgetting_metrics,
    compute_retention_metrics,
    ForgettingResult,
    RetentionMetrics
)

class TestForgettingMetrics:
    """Tests for the forgetting metrics module."""

    def test_load_test_instances_success(self, tmp_path):
        """Test loading valid test instances."""
        data = [
            {"id": "t1", "domain": "logic", "rule_set_id": "r1", "instance_data": {"required_rules": ["rule_a"]}},
            {"id": "t2", "domain": "grid", "rule_set_id": "r2", "instance_data": {"required_rules": ["rule_b"]}}
        ]
        file_path = tmp_path / "test_instances.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_test_instances(str(file_path))
        assert len(result) == 2
        assert result[0]['id'] == 't1'

    def test_load_test_instances_not_found(self):
        """Test loading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_test_instances("non_existent_file.json")

    def test_load_test_instances_invalid_json(self, tmp_path):
        """Test loading invalid JSON raises error."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("not json")
        
        with pytest.raises(json.JSONDecodeError):
            load_test_instances(str(file_path))

    def test_calculate_accuracy_drop(self):
        """Test accuracy drop calculation."""
        assert calculate_accuracy_drop(0.9, 0.7) == 0.2
        assert calculate_accuracy_drop(0.5, 0.5) == 0.0
        assert calculate_accuracy_drop(1.0, 0.0) == 1.0

    def test_calculate_retention_rate(self):
        """Test retention rate calculation."""
        initial = ["a", "b", "c"]
        final = ["a", "b", "d"]
        rate, retained, lost = calculate_retention_rate(initial, final)
        
        assert rate == 2/3
        assert set(retained) == {"a", "b"}
        assert set(lost) == {"c"}
        
        # Edge case: empty initial
        rate, _, _ = calculate_retention_rate([], ["a"])
        assert rate == 0.0

    def test_evaluate_agent_on_instances_empty_instances(self):
        """Test evaluation with no instances."""
        state = {"rule_sets": []}
        acc, count = evaluate_agent_on_instances(state, [])
        assert acc == 0.0
        assert count == 0

    def test_evaluate_agent_on_instances_coverage(self):
        """Test evaluation logic when rules match."""
        # State has rule_a, instance requires rule_a -> should be correct
        state = {
            "rule_sets": [
                {"rule_ids": ["rule_a", "rule_c"]}
            ]
        }
        instances = [
            {"id": "1", "instance_data": {"required_rules": ["rule_a"]}}
        ]
        acc, count = evaluate_agent_on_instances(state, instances)
        assert count == 1
        assert acc == 1.0

    def test_evaluate_agent_on_instances_missing_rules(self):
        """Test evaluation logic when rules are missing."""
        state = {
            "rule_sets": [
                {"rule_ids": ["rule_c"]}
            ]
        }
        instances = [
            {"id": "1", "instance_data": {"required_rules": ["rule_a", "rule_b"]}}
        ]
        acc, count = evaluate_agent_on_instances(state, instances)
        assert count == 1
        # Since required (a, b) is not subset of (c), correct=0
        assert acc == 0.0

    def test_compute_forgetting_metrics_success(self):
        """Test full forgetting metrics computation."""
        state = {
            "initial_state": {
                "rule_sets": [{"rule_ids": ["r1", "r2"]}]
            },
            "final_state": {
                "rule_sets": [{"rule_ids": ["r1"]}]
            }
        }
        instances = [
            {"id": "1", "instance_data": {"required_rules": ["r1"]}}, # Initial: has r1 -> correct. Final: has r1 -> correct.
            {"id": "2", "instance_data": {"required_rules": ["r2"]}}  # Initial: has r2 -> correct. Final: missing r2 -> incorrect.
        ]
        
        result = compute_forgetting_metrics(state, instances, "agent_1", "mixed")
        
        assert result.agent_id == "agent_1"
        assert result.condition == "mixed"
        assert result.initial_accuracy == 1.0 # Both r1 and r2 present
        assert result.final_accuracy == 0.5   # Only r1 present (1/2 correct)
        assert result.accuracy_drop == 0.5

    def test_compute_retention_metrics_success(self):
        """Test full retention metrics computation."""
        state = {
            "initial_state": {
                "rule_sets": [{"rule_ids": ["r1", "r2", "r3"]}]
            },
            "final_state": {
                "rule_sets": [{"rule_ids": ["r1", "r2"]}]
            }
        }
        
        result = compute_retention_metrics(state, "agent_1", "mixed")
        
        assert result.total_rules_initial == 3
        assert result.total_rules_final == 2
        assert result.retained_rules_count == 2
        assert result.retention_rate == 2/3
        assert "r3" in result.lost_rule_ids

    def test_compute_forgetting_metrics_missing_states(self):
        """Test error when states are missing."""
        state = {"initial_state": {}} # Missing final
        with pytest.raises(ValueError):
            compute_forgetting_metrics(state, [], "id", "cond")
        
        state = {"final_state": {}} # Missing initial
        with pytest.raises(ValueError):
            compute_forgetting_metrics(state, [], "id", "cond")
