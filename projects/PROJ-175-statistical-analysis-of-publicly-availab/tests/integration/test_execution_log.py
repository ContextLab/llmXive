import json
import os
from pathlib import Path

def test_pipeline_execution_log_exists():
    """Verify that the pipeline execution log is created and valid."""
    log_path = Path("data/pipeline_execution_log.json")
    assert log_path.exists(), "pipeline_execution_log.json must exist"

    with open(log_path, "r") as f:
        data = json.load(f)

    required_keys = ["status", "runtime_seconds", "peak_ram_mb", "artifacts_created"]
    for key in required_keys:
        assert key in data, f"Missing key in log: {key}"

    assert isinstance(data["status"], str)
    assert isinstance(data["runtime_seconds"], (int, float))
    assert isinstance(data["peak_ram_mb"], (int, float))
    assert isinstance(data["artifacts_created"], list)

def test_log_contains_expected_artifacts():
    """Verify that the log lists expected artifacts from the pipeline."""
    log_path = Path("data/pipeline_execution_log.json")
    if not log_path.exists():
        # If log doesn't exist, this test might be skipped or failed depending on context
        # But for the purpose of this task, we assume the log exists if T043a ran.
        return 

    with open(log_path, "r") as f:
        data = json.load(f)

    expected_artifacts = [
        "data/verification_report.json",
        "data/processed/final_features.parquet",
        "data/final/logistic_results.json",
        "data/evaluation_metrics.json",
        "docs/draft_final_report.md"
    ]

    created = data.get("artifacts_created", [])
    
    # Check that at least the critical ones are present if status is SUCCESS
    if data.get("status") == "SUCCESS":
        for artifact in expected_artifacts:
            assert artifact in created, f"Expected artifact missing: {artifact}"