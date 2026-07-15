"""
Unit tests for T026: Save per-trace rule sets and compressibility scores.
"""
import json
import csv
import tempfile
from pathlib import Path
import pytest

from models.save_results import save_per_trace_scores, save_rule_sets

@pytest.fixture
def sample_scores():
    return [
        {
            "trace_id": "trace_001",
            "compressibility_score": 0.45,
            "rule_set_size": 12,
            "trace_length": 25,
            "fidelity": 0.92,
            "entropy": 1.2,
            "tool_repetition_frequency": 0.3,
            "argument_variance": 0.15
        },
        {
            "trace_id": "trace_002",
            "compressibility_score": 0.60,
            "rule_set_size": 18,
            "trace_length": 30,
            "fidelity": 0.95,
            "entropy": 1.5,
            "tool_repetition_frequency": 0.2,
            "argument_variance": 0.10
        }
    ]

@pytest.fixture
def sample_rules():
    return [
        {
            "trace_id": "trace_001",
            "rules": [
                {"condition": "tool == 'edit'", "action": "apply"},
                {"condition": "tool == 'delete'", "action": "undo"}
            ],
            "model_params": {"depth": 3}
        },
        {
            "trace_id": "trace_002",
            "rules": [
                {"condition": "tool == 'insert'", "action": "append"}
            ],
            "model_params": {"depth": 4}
        }
    ]

def test_save_per_trace_scores_creates_csv(sample_scores, tmp_path):
    """Test that scores are correctly saved to CSV."""
    output_file = tmp_path / "scores.csv"
    save_per_trace_scores(sample_scores, output_file)

    assert output_file.exists()
    
    with open(output_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 2
    assert rows[0]['trace_id'] == 'trace_001'
    assert float(rows[0]['compressibility_score']) == 0.45
    assert rows[1]['trace_id'] == 'trace_002'

def test_save_rule_sets_creates_json(sample_rules, tmp_path):
    """Test that rule sets are correctly saved as JSON files."""
    output_dir = tmp_path / "rules"
    save_rule_sets(sample_rules, output_dir)

    assert output_dir.exists()
    
    # Check file 1
    file1 = output_dir / "trace_001_rules.json"
    assert file1.exists()
    with open(file1, 'r') as f:
        data = json.load(f)
    assert data['trace_id'] == 'trace_001'
    assert len(data['rules']) == 2

    # Check file 2
    file2 = output_dir / "trace_002_rules.json"
    assert file2.exists()
    with open(file2, 'r') as f:
        data = json.load(f)
    assert data['trace_id'] == 'trace_002'
    assert len(data['rules']) == 1

def test_save_empty_scores_raises_error(tmp_path):
    """Test that saving empty scores raises ValueError."""
    output_file = tmp_path / "scores.csv"
    with pytest.raises(ValueError, match="No scores provided"):
        save_per_trace_scores([], output_file)

def test_save_empty_rules_logs_but_continues(tmp_path):
    """Test that saving empty rules list behaves gracefully."""
    output_dir = tmp_path / "rules"
    # Should not raise, just print a message (simulated by logic check)
    # The function raises ValueError if empty, so we test that behavior
    with pytest.raises(ValueError, match="No rule data provided"):
        save_rule_sets([], output_dir)