"""
Unit tests for code/rules/uncertainty_flagger.py

Tests the logic for flagging "Extraction Uncertainty" and calculating
excluded_metrics as per FR-004.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from rules.uncertainty_flagger import UncertaintyFlagger, UncertaintyFlag, UncertaintyReport
from rules.extractor import ExtractedRule


@pytest.fixture
def temp_files():
    """Creates temporary files for Oracle, Rules, and Traces."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create Mock Oracle
        oracle_data = {
            "state_1": {"valid_actions": ["move_left", "move_right", "pickup"]},
            "state_2": {"valid_actions": ["move_left", "move_right", "drop"]}
        }
        oracle_path = tmpdir_path / "oracle_graph.json"
        with open(oracle_path, 'w') as f:
            json.dump(oracle_data, f)
        
        # Create Mock Rules
        rules_data = {
            "rules": [
                {
                    "id": "rule_1",
                    "task_type": "navigation",
                    "action": "move_left",
                    "condition": "wall_left == False",
                    "confidence": 0.9,
                    "possible_rules": [],
                    "metadata": {"confidence": 0.9}
                },
                {
                    "id": "rule_2",
                    "task_type": "navigation",
                    "action": "move_right",
                    "condition": "wall_right == False",
                    "confidence": 0.5, # Low confidence -> Ambiguous
                    "possible_rules": [],
                    "metadata": {"confidence": 0.5}
                }
            ]
        }
        rules_path = tmpdir_path / "extracted_rules.json"
        with open(rules_path, 'w') as f:
            json.dump(rules_data, f)
        
        # Create Mock Traces
        traces_data = [
            {"id": "trace_1", "task_type": "navigation", "initial_state_id": "state_1", "cot": "..."},
            {"id": "trace_2", "task_type": "navigation", "initial_state_id": "state_1", "cot": "..."},
            {"id": "trace_3", "task_type": "unknown_type", "initial_state_id": "state_1", "cot": "..."} # Cold start
        ]
        traces_path = tmpdir_path / "cot_traces.json"
        with open(traces_path, 'w') as f:
            json.dump(traces_data, f)
        
        yield {
            "oracle": str(oracle_path),
            "rules": str(rules_path),
            "traces": str(traces_path),
            "output": str(tmpdir_path / "uncertainty_report.json")
        }


def test_flagger_initialization(temp_files):
    """Test that the flagger loads data correctly."""
    flagger = UncertaintyFlagger(
        temp_files["oracle"],
        temp_files["rules"],
        temp_files["traces"]
    )
    flagger.load_data()
    
    assert len(flagger.oracle_graph) == 2
    assert len(flagger.extracted_rules) == 2
    assert len(flagger.traces) == 3


def test_ambiguity_detection(temp_files):
    """Test that low confidence rules are flagged as ambiguous."""
    flagger = UncertaintyFlagger(
        temp_files["oracle"],
        temp_files["rules"],
        temp_files["traces"]
    )
    report = flagger.flag_uncertainties()
    
    # trace_2 should be flagged as ambiguous due to low confidence (0.5)
    ambiguous_flags = [f for f in report.flags if f.type == "ambiguous"]
    assert len(ambiguous_flags) >= 1
    assert any(f.trace_id == "trace_2" for f in ambiguous_flags)


def test_cold_start_detection(temp_files):
    """Test that task types with no rules are flagged as cold start."""
    flagger = UncertaintyFlagger(
        temp_files["oracle"],
        temp_files["rules"],
        temp_files["traces"]
    )
    report = flagger.flag_uncertainties()
    
    # trace_3 has task_type "unknown_type" which has no rules
    cold_flags = [f for f in report.flags if f.type == "cold_start"]
    assert len(cold_flags) >= 1
    assert any(f.trace_id == "trace_3" for f in cold_flags)
    
    assert report.excluded_metrics["cold_start"] >= 1


def test_excluded_metrics_structure(temp_files):
    """Test that excluded_metrics contains the required fields."""
    flagger = UncertaintyFlagger(
        temp_files["oracle"],
        temp_files["rules"],
        temp_files["traces"]
    )
    report = flagger.flag_uncertainties()
    
    assert "extraction_uncertainty" in report.excluded_metrics
    assert "cold_start" in report.excluded_metrics
    assert isinstance(report.excluded_metrics["extraction_uncertainty"], int)
    assert isinstance(report.excluded_metrics["cold_start"], int)


def test_save_report(temp_files):
    """Test that the report is saved to the correct path."""
    flagger = UncertaintyFlagger(
        temp_files["oracle"],
        temp_files["rules"],
        temp_files["traces"]
    )
    flagger.save_report(temp_files["output"])
    
    assert os.path.exists(temp_files["output"])
    
    with open(temp_files["output"], 'r') as f:
        saved_data = json.load(f)
    
    assert "excluded_metrics" in saved_data
    assert "flags" in saved_data
    assert "total_traces" in saved_data