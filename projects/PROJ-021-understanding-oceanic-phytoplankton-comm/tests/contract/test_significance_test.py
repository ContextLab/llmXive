import json
import os
import pytest
from pathlib import Path

def test_significance_test_schema():
    """Contract test for significance_test.json schema."""
    # This test verifies the structure of the significance test output
    # It should be run after the evaluation script has generated the artifact
    
    # Note: This test will fail if the artifact doesn't exist yet
    # which is expected before the first successful run
    artifact_path = Path("data/artifacts/significance_test.json")
    
    if not artifact_path.exists():
        pytest.skip("Significance test artifact not yet generated")
    
    with open(artifact_path, 'r') as f:
        result = json.load(f)
    
    # Verify required fields
    assert "test_type" in result
    assert "confidence_level" in result
    assert "threshold_difference" in result
    assert "status" in result
    
    # Verify status is one of the expected values
    valid_statuses = [
        "VLM Significantly Exceeds Baseline",
        "VLM Significantly Different but Below Threshold",
        "VLM Exceeds Threshold but Not Statistically Significant",
        "VLM Does Not Exceed Baseline",
        "VLM Failed to Exceed Baseline",
        "No valid data pairs for comparison",
        "Test Failed: ..."
    ]
    
    # Check if status matches expected pattern
    status_valid = any(s in result["status"] for s in valid_statuses) or result["status"] == "N/A"
    assert status_valid, f"Unexpected status: {result['status']}"
    
    # If VLM fallback, p_value should be "N/A"
    if "VLM Failed" in result["status"]:
        assert result.get("p_value") == "N/A" or result.get("p_value") == "ERROR"
    
    # If not fallback, p_value should be numeric or "ERROR"
    if "VLM Failed" not in result["status"] and "Test Failed" not in result["status"]:
        assert isinstance(result.get("p_value"), (int, float)) or result.get("p_value") == "N/A"

def test_significance_test_logic():
    """Test the logic of significance test results."""
    artifact_path = Path("data/artifacts/significance_test.json")
    
    if not artifact_path.exists():
        pytest.skip("Significance test artifact not yet generated")
    
    with open(artifact_path, 'r') as f:
        result = json.load(f)
    
    # Verify threshold difference is 0.05 as per spec
    assert result.get("threshold_difference") == 0.05
    
    # Verify confidence level is 0.95 (95%)
    assert result.get("confidence_level") == 0.95
    
    # Verify test type is paired t-test
    assert "t-test" in result.get("test_type", "").lower()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])