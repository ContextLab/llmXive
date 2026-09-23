"""
Integration tests for CoT quality metrics calculation.

These tests verify the end-to-end calculation of Pattern Reproduction Precision
using realistic synthetic control traces and extracted rules.
"""

import json
import pytest
from pathlib import Path
from analysis.metrics import (
    calculate_pattern_reproduction_precision,
    save_metrics,
    PatternReproductionResult
)


@pytest.fixture
def integration_test_data(tmp_path):
    """Create integration test data files."""
    traces_path = tmp_path / "synthetic_control_traces.json"
    rules_path = tmp_path / "extracted_rules.json"
    output_path = tmp_path / "cot_quality_metrics.json"

    # Create comprehensive synthetic control traces
    traces = [
        {"pattern_id": "spatial_navigation", "action": "move", "context": "grid_world"},
        {"pattern_id": "temporal_planning", "action": "wait", "context": "time_sensitive"},
        {"pattern_id": "causal_reasoning", "action": "interact", "context": "object_manipulation"},
        {"pattern_id": "conditional_logic", "action": "check", "context": "precondition"},
        {"pattern_id": "hierarchical_task", "action": "subtask", "context": "decomposition"},
        {"pattern_id": "spatial_navigation", "action": "move", "context": "obstacle_avoidance"},
        {"pattern_id": "temporal_planning", "action": "sequence", "context": "ordered_steps"},
        {"pattern_id": "causal_reasoning", "action": "predict", "context": "consequence"}
    ]
    with open(traces_path, 'w') as f:
        json.dump(traces, f)

    # Create extracted rules that match most patterns
    rules = [
        {"pattern_id": "spatial_navigation", "condition": "goal_visible", "conclusion": "navigate"},
        {"pattern_id": "temporal_planning", "condition": "deadline_approaching", "conclusion": "plan"},
        {"pattern_id": "causal_reasoning", "condition": "action_possible", "conclusion": "execute"},
        {"pattern_id": "conditional_logic", "condition": "state_check", "conclusion": "verify"},
        {"pattern_id": "hierarchical_task", "condition": "complex_goal", "conclusion": "decompose"}
    ]
    with open(rules_path, 'w') as f:
        json.dump(rules, f)

    return {
        "traces_path": traces_path,
        "rules_path": rules_path,
        "output_path": output_path
    }


def test_integration_pattern_reproduction_precision(integration_test_data):
    """Test end-to-end pattern reproduction precision calculation."""
    result = calculate_pattern_reproduction_precision(
        integration_test_data["traces_path"],
        integration_test_data["rules_path"]
    )

    # Verify results
    assert result.total_patterns == 5  # Unique pattern IDs
    assert result.reproduced_patterns == 5  # All matched
    assert result.precision == 1.0
    assert len(result.unmatched_patterns) == 0


def test_integration_save_and_load_metrics(integration_test_data):
    """Test saving and loading metrics."""
    # Calculate result
    result = calculate_pattern_reproduction_precision(
        integration_test_data["traces_path"],
        integration_test_data["rules_path"]
    )

    # Save metrics
    save_metrics(result, integration_test_data["output_path"])

    # Verify file exists and can be loaded
    assert integration_test_data["output_path"].exists()

    with open(integration_test_data["output_path"], 'r') as f:
        loaded_data = json.load(f)

    assert loaded_data["pattern_reproduction_precision"] == 1.0
    assert loaded_data["threshold_met"] is True


def test_integration_threshold_validation(integration_test_data):
    """Test that threshold validation works correctly."""
    result = calculate_pattern_reproduction_precision(
        integration_test_data["traces_path"],
        integration_test_data["rules_path"]
    )

    # Verify threshold is correctly evaluated
    assert result.metadata["threshold"] == 0.95
    assert result.metadata["threshold_met"] is True


def test_integration_partial_match(integration_test_data):
    """Test with partial pattern matching."""
    # Modify rules to only match some patterns
    partial_rules = [
        {"pattern_id": "spatial_navigation", "condition": "goal_visible", "conclusion": "navigate"},
        {"pattern_id": "temporal_planning", "condition": "deadline_approaching", "conclusion": "plan"}
    ]
    integration_test_data["rules_path"].write_text(json.dumps(partial_rules))

    result = calculate_pattern_reproduction_precision(
        integration_test_data["traces_path"],
        integration_test_data["rules_path"]
    )

    # Should have lower precision
    assert result.precision == 0.4  # 2/5
    assert result.metadata["threshold_met"] is False
    assert len(result.unmatched_patterns) == 3
    assert "causal_reasoning" in result.unmatched_patterns
    assert "conditional_logic" in result.unmatched_patterns
    assert "hierarchical_task" in result.unmatched_patterns


def test_integration_empty_patterns(integration_test_data):
    """Test with traces that have no pattern IDs."""
    # Create traces without pattern_id
    empty_traces = [
        {"action": "move", "context": "test"},
        {"action": "wait", "context": "test"}
    ]
    integration_test_data["traces_path"].write_text(json.dumps(empty_traces))

    result = calculate_pattern_reproduction_precision(
        integration_test_data["traces_path"],
        integration_test_data["rules_path"]
    )

    assert result.total_patterns == 0
    assert result.precision == 0.0
    assert "error" in result.metadata