"""
Integration tests for T021b: Sensitivity Report Aggregation.

Tests the aggregation logic by creating mock inputs for T021a and T023c,
running the aggregator, and verifying the output schema and content.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects" / "PROJ-903-llmxive-follow-up-extending-data-journal" / "code"))

from narrative.sensitivity_aggregator import aggregate_sensitivity_report, run_aggregation_pipeline, OUTPUT_DIR, SENSITIVITY_INPUT_PATH, STABILITY_INPUT_PATH, FINAL_REPORT_PATH

@pytest.fixture
def mock_sweep_data():
    """Mock data simulating T021a output."""
    return [
        {
            "candidate_index": 0,
            "threshold_config": "p<0.05, r>0.15",
            "claim": "Higher income correlates with better housing",
            "p_value": 0.03,
            "partial_r": 0.25
        },
        {
            "candidate_index": 0,
            "threshold_config": "p<0.01, r>0.2",
            "claim": "NO_SIGNIFICANT_COUNTERFACTUAL",
            "p_value": 0.08,
            "partial_r": 0.12
        },
        {
            "candidate_index": 1,
            "threshold_config": "p<0.05, r>0.15",
            "claim": "Crime rate inversely correlates with property value",
            "p_value": 0.01,
            "partial_r": -0.45
        }
    ]

@pytest.fixture
def mock_stability_data():
    """Mock data simulating T023c output."""
    return [
        {
            "candidate_index": 0,
            "stability_score": 0.85,
            "validity_status": "verified"
        },
        {
            "candidate_index": 1,
            "stability_score": 0.40,
            "validity_status": "confounded"
        }
    ]

def test_aggregate_sensitivity_report(mock_sweep_data, mock_stability_data):
    """Test the core aggregation logic."""
    result = aggregate_sensitivity_report(mock_sweep_data, mock_stability_data)
    
    assert isinstance(result, list)
    assert len(result) == 3 # Should have 3 entries matching sweep data
    
    # Check first entry (candidate 0, valid)
    entry1 = result[0]
    assert entry1["candidate_index"] == 0
    assert entry1["threshold_config"] == "p<0.05, r>0.15"
    assert entry1["claim"] == "Higher income correlates with better housing"
    assert entry1["p_value"] == 0.03
    assert entry1["partial_r"] == 0.25
    assert entry1["stability_score"] == 0.85
    assert entry1["validity_status"] == "verified"
    
    # Check third entry (candidate 1, confounded)
    entry3 = result[2]
    assert entry3["candidate_index"] == 1
    assert entry3["stability_score"] == 0.40
    assert entry3["validity_status"] == "confounded"
    
    # Check schema completeness
    required_keys = {"threshold_config", "claim", "p_value", "partial_r", "stability_score", "validity_status"}
    for entry in result:
        assert required_keys.issubset(entry.keys()), f"Missing keys in entry: {entry.keys()}"

def test_aggregate_missing_stability_data(mock_sweep_data):
    """Test handling when stability data is missing for a candidate."""
    # Stability data missing for candidate 1
    stability_data = [
        {
            "candidate_index": 0,
            "stability_score": 0.85,
            "validity_status": "verified"
        }
    ]
    
    result = aggregate_sensitivity_report(mock_sweep_data, stability_data)
    
    # Candidate 1 entries should be marked as failed
    entry3 = result[2] # Candidate 1
    assert entry3["stability_score"] == 0.0
    assert entry3["validity_status"] == "failed"

@pytest.mark.integration
def test_full_aggregation_pipeline(tmp_path):
    """Test the full pipeline with temporary files."""
    # Create temporary input files
    sweep_path = tmp_path / "sensitivity_sweep.json"
    stability_path = tmp_path / "stability_analysis.json"
    output_path = tmp_path / "sensitivity_report.json"
    
    sweep_data = [
        {"candidate_index": 0, "threshold_config": "test", "claim": "test", "p_value": 0.01, "partial_r": 0.2}
    ]
    stability_data = [
        {"candidate_index": 0, "stability_score": 0.9, "validity_status": "verified"}
    ]
    
    with open(sweep_path, 'w') as f:
        json.dump(sweep_data, f)
    with open(stability_path, 'w') as f:
        json.dump(stability_data, f)
    
    # Patch the global paths
    with patch("narrative.sensitivity_aggregator.SENSITIVITY_INPUT_PATH", sweep_path), \
         patch("narrative.sensitivity_aggregator.STABILITY_INPUT_PATH", stability_path), \
         patch("narrative.sensitivity_aggregator.FINAL_REPORT_PATH", output_path):
        
        success = run_aggregation_pipeline()
        
        assert success
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            result = json.load(f)
        
        assert len(result) == 1
        assert result[0]["validity_status"] == "verified"
        assert result[0]["stability_score"] == 0.9