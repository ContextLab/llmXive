"""
Contract test for T018: Verify trend_results.json aggregation schema.
Ensures the output of generate_trend_results.py matches the expected structure.
"""
import json
import os
import pytest
from pathlib import Path

# Adjust import path for local testing if needed, but assumes installed package or PYTHONPATH set
# For this test, we assume the artifact exists on disk after T018 runs.

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
TREND_RESULTS_PATH = DATA_DIR / "trend_results.json"

def load_trend_results():
    if not TREND_RESULTS_PATH.exists():
        pytest.skip(f"Artifact {TREND_RESULTS_PATH} not found. Run T018 first.")
    with open(TREND_RESULTS_PATH, 'r') as f:
        return json.load(f)

def test_trend_results_schema():
    """
    Verify the top-level schema of trend_results.json.
    Must contain 'metadata' and 'results' keys.
    """
    data = load_trend_results()
    
    assert "metadata" in data, "Missing 'metadata' key in trend_results.json"
    assert "results" in data, "Missing 'results' key in trend_results.json"
    assert isinstance(data["results"], list), "'results' must be a list"

def test_metadata_structure():
    """
    Verify metadata contains source file references.
    """
    data = load_trend_results()
    meta = data["metadata"]
    
    assert "source_files" in meta, "Missing 'source_files' in metadata"
    sources = meta["source_files"]
    assert "trends" in sources, "Missing 'trends' source file reference"
    assert "confidence_intervals" in sources, "Missing 'confidence_intervals' source file reference"
    assert "correlations" in sources, "Missing 'correlations' source file reference"

def test_result_record_schema():
    """
    Verify each result record contains trend, CI, and correlation data.
    """
    data = load_trend_results()
    
    if not data["results"]:
        pytest.skip("No results to test.")

    record = data["results"][0]
    
    # Trend data fields (from T014)
    assert "tag" in record, "Missing 'tag' in result record"
    assert "slope" in record, "Missing 'slope' (Theil-Sen) in result record"
    assert "p_value" in record, "Missing 'p_value' in result record"
    assert "classification" in record, "Missing 'classification' in result record"
    
    # Classification must be valid
    valid_classifications = ["Growth", "Decline", "Stable", "Insufficient Data"]
    assert record["classification"] in valid_classifications, \
        f"Invalid classification: {record['classification']}"

    # CI data (from T016)
    assert "confidence_interval" in record, "Missing 'confidence_interval' key"
    if record["confidence_interval"] is not None:
        ci = record["confidence_interval"]
        assert "lower_bound" in ci, "Missing 'lower_bound' in confidence_interval"
        assert "upper_bound" in ci, "Missing 'upper_bound' in confidence_interval"
    
    # Correlation data (from T040)
    assert "correlation" in record, "Missing 'correlation' key"
    if record["correlation"] is not None:
        corr = record["correlation"]
        assert "external_metric" in corr, "Missing 'external_metric' in correlation"
        assert "pearson_r" in corr, "Missing 'pearson_r' in correlation"
        assert "p_value" in corr, "Missing 'p_value' in correlation"

def test_classification_logic():
    """
    Verify that classifications align with p-values and power (if available).
    """
    data = load_trend_results()
    
    for record in data["results"]:
        p_val = record.get("p_value")
        classification = record.get("classification")
        
        if classification == "Insufficient Data":
            # Per FR-013: p >= 0.05 AND power < 0.8
            # We assume power is present if available, but strictly checking p-value logic here
            assert p_val is not None and p_val >= 0.05, \
                f"Classification 'Insufficient Data' requires p >= 0.05, got {p_val}"
        elif classification == "Stable":
            # Per FR-013: p >= 0.05 AND power >= 0.8
            assert p_val is not None and p_val >= 0.05, \
                f"Classification 'Stable' requires p >= 0.05, got {p_val}"
        elif classification in ["Growth", "Decline"]:
            # Significant trend
            assert p_val is not None and p_val < 0.05, \
                f"Classification '{classification}' requires p < 0.05, got {p_val}"

def test_hash_consistency_in_state():
    """
    Verify that the state file was updated with the correct hash for trend_results.json.
    This tests the FR-012 requirement.
    """
    import hashlib
    from utils.state_manager import load_state, calculate_sha256
    
    state_path = PROJECT_ROOT / "state" / "projects" / "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
    if not state_path.exists():
        pytest.skip("State file not found. Ensure T009/T018 has run.")
    
    # Calculate actual hash
    actual_hash = calculate_sha256(TREND_RESULTS_PATH)
    
    # Load state
    state = load_state(state_path)
    
    # Check if artifact is tracked
    if "artifacts" not in state or "checksums" not in state:
        pytest.skip("State file structure incomplete.")
    
    checksums = state.get("checksums", {})
    assert "trend_results.json" in checksums, \
        "trend_results.json not found in state checksums. T018 must update state."
    
    stored_hash = checksums["trend_results.json"]
    assert stored_hash == actual_hash, \
        f"Hash mismatch for trend_results.json. Stored: {stored_hash}, Actual: {actual_hash}"