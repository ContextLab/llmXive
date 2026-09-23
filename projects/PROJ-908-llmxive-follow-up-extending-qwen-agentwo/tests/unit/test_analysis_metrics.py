"""
Unit tests for code/analysis/metrics.py
"""

import json
import tempfile
from pathlib import Path

import pytest

from analysis.metrics import (
    load_synthetic_control_traces,
    load_extracted_rules,
    extract_pattern_ids_from_traces,
    match_patterns_to_rules,
    calculate_pattern_reproduction_precision,
    save_metrics,
    PatternReproductionResult,
    PatternMatch
)


@pytest.fixture
def sample_traces():
    return [
        {
            "pattern_id": "pattern_A",
            "steps": [
                {"action": "move_north", "logical_form": "move(current, north)"},
                {"action": "pick_up", "logical_form": "pick_up(current, object)"}
            ]
        },
        {
            "pattern_id": "pattern_B",
            "steps": [
                {"action": "move_south", "logical_form": "move(current, south)"},
                {"action": "drop", "logical_form": "drop(current, object)"}
            ]
        }
    ]


@pytest.fixture
def sample_rules():
    return [
        {
            "id": "rule_1",
            "signature": "move(current, north)",
            "logical_form": "move(X, north) :- at(X, Y)"
        },
        {
            "id": "rule_2",
            "signature": "pick_up(current, object)",
            "logical_form": "pick_up(X, Y) :- at(X, Y), has_space(X)"
        }
    ]


@pytest.fixture
def temp_traces_file(sample_traces):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_traces, f)
        path = Path(f.name)
    yield path
    path.unlink()


@pytest.fixture
def temp_rules_file(sample_rules):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_rules, f)
        path = Path(f.name)
    yield path
    path.unlink()


def test_load_synthetic_control_traces(temp_traces_file, sample_traces):
    traces = load_synthetic_control_traces(temp_traces_file)
    assert len(traces) == len(sample_traces)
    assert traces[0]["pattern_id"] == "pattern_A"


def test_load_synthetic_control_traces_missing_file():
    with pytest.raises(FileNotFoundError):
        load_synthetic_control_traces(Path("nonexistent.json"))


def test_load_extracted_rules(temp_rules_file, sample_rules):
    rules = load_extracted_rules(temp_rules_file)
    assert len(rules) == len(sample_rules)
    assert rules[0]["id"] == "rule_1"


def test_load_extracted_rules_missing_file():
    with pytest.raises(FileNotFoundError):
        load_extracted_rules(Path("nonexistent.json"))


def test_extract_pattern_ids_from_traces(sample_traces):
    ids = extract_pattern_ids_from_traces(sample_traces)
    assert ids == {"pattern_A", "pattern_B"}


def test_match_patterns_to_rules(sample_traces, sample_rules):
    matches = match_patterns_to_rules(sample_traces, sample_rules)
    assert len(matches) == 2
    # pattern_A should match rule_1 and rule_2 (high confidence)
    assert matches[0].pattern_id == "pattern_A"
    assert matches[0].matched_rule_id is not None
    assert matches[0].confidence >= 0.8


def test_calculate_pattern_reproduction_precision(sample_traces, sample_rules):
    result = calculate_pattern_reproduction_precision(sample_traces, sample_rules)
    assert isinstance(result, PatternReproductionResult)
    assert result.total_patterns == 2
    assert result.precision >= 0.0
    assert result.precision <= 1.0


def test_save_metrics():
    result = PatternReproductionResult(
        total_patterns=10,
        reproduced_patterns=9,
        precision=0.9,
        matches=[],
        metadata={"test": "value"}
    )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        path = Path(f.name)

    save_metrics(result, path)
    assert path.exists()

    with open(path, 'r') as f:
        saved = json.load(f)

    assert saved["total_patterns"] == 10
    assert saved["precision"] == 0.9
    path.unlink()


def test_pattern_reproduction_precision_empty_traces(sample_rules):
    result = calculate_pattern_reproduction_precision([], sample_rules)
    assert result.total_patterns == 0
    assert result.precision == 0.0


def test_pattern_reproduction_precision_empty_rules(sample_traces):
    result = calculate_pattern_reproduction_precision(sample_traces, [])
    assert result.total_patterns == 2
    assert result.reproduced_patterns == 0
    assert result.precision == 0.0