import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.preprocess import check_confounding

@pytest.fixture
def sample_linked_trials():
    """Create a sample linked_trials.csv for testing."""
    data = {
        'trial_id': [f't{i}' for i in range(100)],
        'response_time': [500 + i * 10 for i in range(100)],
        'stimulus_id': [f's{i % 10}' for i in range(100)],
        'prime_condition': ['prime_A'] * 50 + ['prime_B'] * 50,
        'participant_id': ['p1'] * 100,
        'trial_order': list(range(100))
    }
    return pd.DataFrame(data)

@pytest.fixture
def confounded_linked_trials():
    """Create a sample linked_trials.csv with confounding (prime_A only in first half)."""
    data = {
        'trial_id': [f't{i}' for i in range(100)],
        'response_time': [500 + i * 10 for i in range(100)],
        'stimulus_id': [f's{i % 10}' for i in range(100)],
        'prime_condition': ['prime_A'] * 60 + ['prime_B'] * 40, # Heavily skewed
        'participant_id': ['p1'] * 100,
        'trial_order': list(range(100))
    }
    return pd.DataFrame(data)

def test_confounding_check_pass(sample_linked_trials, tmp_path):
    """Test that a balanced design passes the confounding check."""
    input_file = tmp_path / "linked_trials.csv"
    output_file = tmp_path / "confounding_report.json"
    
    sample_linked_trials.to_csv(input_file, index=False)
    
    # This should not raise an error
    result = check_confounding(
        input_path=str(input_file),
        output_path=str(output_file)
    )
    
    assert result["confounding_detected"] is False
    assert result["confounding_status"] == "passed" if "confounding_status" in result else True
    
    # Verify output file exists
    assert output_file.exists()
    
    # Verify content
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    assert report["confounding_detected"] is False
    assert "prime_vs_trial_order" in report["details"]
    assert report["details"]["prime_vs_trial_order"]["status"] == "PASS"

def test_confounding_check_fail(confounded_linked_trials, tmp_path):
    """Test that a confounded design raises an error."""
    input_file = tmp_path / "linked_trials.csv"
    output_file = tmp_path / "confounding_report.json"
    
    confounded_linked_trials.to_csv(input_file, index=False)
    
    # This should raise a ValueError
    with pytest.raises(ValueError, match="Confounding detected"):
        check_confounding(
            input_path=str(input_file),
            output_path=str(output_file)
        )

def test_missing_input_file(tmp_path):
    """Test that missing input file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        check_confounding(
            input_path=str(tmp_path / "nonexistent.csv"),
            output_path=str(tmp_path / "report.json")
        )

def test_report_structure(sample_linked_trials, tmp_path):
    """Test that the report contains all required keys."""
    input_file = tmp_path / "linked_trials.csv"
    output_file = tmp_path / "confounding_report.json"
    
    sample_linked_trials.to_csv(input_file, index=False)
    
    check_confounding(
        input_path=str(input_file),
        output_path=str(output_file)
    )
    
    with open(output_file, 'r') as f:
        report = json.load(f)
    
    required_keys = [
        "check_timestamp", "input_file", "checks_performed", 
        "correlation_matrix", "confounding_detected", "details"
    ]
    
    for key in required_keys:
        assert key in report, f"Missing key: {key}"