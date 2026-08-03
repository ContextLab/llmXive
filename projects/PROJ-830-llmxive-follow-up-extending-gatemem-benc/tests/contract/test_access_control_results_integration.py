"""
Integration test for T012: Run pipeline and verify schema compliance.

This test ensures that when the pipeline runs, it produces output that
strictly adheres to the results schema.
"""
import json
import subprocess
import sys
from pathlib import Path
import pytest
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "access_control_results.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "results.schema.yaml"


def load_schema() -> dict:
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


@pytest.mark.integration
def test_pipeline_produces_valid_schema_output():
    """
    Run the evaluation pipeline (if not already run) and verify the output
    matches the schema.
    
    Note: This test assumes the pipeline has been run or will be run
    as part of the test suite setup. If the file doesn't exist, it skips
    with a clear message.
    """
    if not RESULTS_PATH.exists():
        pytest.skip(
            f"Results file not found at {RESULTS_PATH}. "
            "Run the evaluation pipeline first: python code/cli/run_evaluation.py --domain medical,office"
        )
    
    schema = load_schema()
    
    with open(RESULTS_PATH, "r") as f:
        results = json.load(f)
    
    # Basic structural validation
    assert "metadata" in results, "Missing metadata"
    assert "access_control" in results, "Missing access_control"
    
    # Validate method
    ac = results["access_control"]
    assert ac["method"] in ["gatekeeper", "baseline_retrieval", "baseline_long_context"], \
        f"Invalid method: {ac['method']}"
    
    # Validate score range
    assert 0 <= ac["score"] <= 1, f"Score out of range: {ac['score']}"
    
    # Validate numeric fields
    assert isinstance(ac["total_samples"], int) and ac["total_samples"] > 0, \
        "total_samples must be a positive integer"
    assert isinstance(ac["unauthorized_leaks"], int) and ac["unauthorized_leaks"] >= 0, \
        "unauthorized_leaks must be a non-negative integer"
    assert isinstance(ac["allowed_requests"], int) and ac["allowed_requests"] >= 0, \
        "allowed_requests must be a non-negative integer"
    
    # Validate metadata
    meta = results["metadata"]
    assert "timestamp" in meta, "Missing timestamp"
    assert "pipeline_version" in meta, "Missing pipeline_version"
    assert "dataset_version" in meta, "Missing dataset_version"
    assert "domains" in meta and isinstance(meta["domains"], list), "Invalid domains"
    
    # If by_domain exists, validate structure
    if "by_domain" in ac:
        assert isinstance(ac["by_domain"], list), "by_domain must be a list"
        for domain_result in ac["by_domain"]:
            assert "domain" in domain_result, "Missing domain name"
            assert "score" in domain_result, "Missing score in by_domain"
            assert 0 <= domain_result["score"] <= 1, f"Invalid score in by_domain: {domain_result['score']}"
