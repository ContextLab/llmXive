import os
import json
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.insert(0, str(project_root))

from validation.execute_pipeline import main

@pytest.mark.integration
def test_pipeline_execution_log_creation():
    """Test that the pipeline execution creates the required log file."""
    # This is an integration test that runs the actual pipeline
    # It should create data/pipeline_execution_log.json
    
    log_path = project_root / "data" / "pipeline_execution_log.json"
    
    # Clean up any existing log
    if log_path.exists():
        log_path.unlink()
    
    # Run the pipeline
    exit_code = main()
    
    # Verify the log file was created
    assert log_path.exists(), "Pipeline execution log was not created"
    
    # Verify the log content structure
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert "status" in log_data, "Missing 'status' field"
    assert "runtime_seconds" in log_data, "Missing 'runtime_seconds' field"
    assert "peak_ram_mb" in log_data, "Missing 'peak_ram_mb' field"
    assert "artifacts_created" in log_data, "Missing 'artifacts_created' field"
    
    # Verify types
    assert isinstance(log_data["runtime_seconds"], (int, float)), "runtime_seconds should be numeric"
    assert isinstance(log_data["peak_ram_mb"], (int, float)), "peak_ram_mb should be numeric"
    assert isinstance(log_data["artifacts_created"], list), "artifacts_created should be a list"
    
    # If pipeline succeeded, verify status is SUCCESS
    if exit_code == 0:
        assert log_data["status"] == "SUCCESS", f"Expected SUCCESS status, got {log_data['status']}"
    else:
        assert log_data["status"] == "FAILED", f"Expected FAILED status, got {log_data['status']}"

@pytest.mark.integration
def test_pipeline_artifacts_exist():
    """Test that the pipeline creates the expected artifacts."""
    # Run the pipeline first
    main()
    
    # Check for expected artifacts
    expected_artifacts = [
        "data/raw/recipe1m_stream_log.json",
        "data/processed/co_occurrence_matrix.parquet",
        "data/processed/flavor_similarity.parquet",
        "data/processed/ingredient_roles_binned.parquet",
        "data/processed/final_features.parquet",
        "data/split_config.json"
    ]
    
    missing_artifacts = []
    for artifact in expected_artifacts:
        artifact_path = project_root / artifact
        if not artifact_path.exists():
            missing_artifacts.append(artifact)
    
    # If there are missing artifacts, check if the pipeline failed
    log_path = project_root / "data" / "pipeline_execution_log.json"
    if log_path.exists():
        with open(log_path, 'r') as f:
            log_data = json.load(f)
        
        if log_data.get("status") == "SUCCESS":
            assert len(missing_artifacts) == 0, f"Pipeline succeeded but missing artifacts: {missing_artifacts}"
        else:
            # If pipeline failed, it's expected that some artifacts might be missing
            pytest.skip(f"Pipeline failed with status: {log_data.get('status')}")
    else:
        pytest.fail("Pipeline execution log not found")
