"""
Integration Test for T035: Quickstart Validation
Verifies that the pipeline runs end-to-end and produces expected artifacts.
"""
import os
import sys
import pytest
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

@pytest.fixture(scope="module")
def pipeline_output():
    """
    Runs the quickstart validation script once per test session.
    Returns the exit code and output path.
    """
    script_path = project_root / "code" / "run_quickstart_validation.py"
    if not script_path.exists():
        pytest.skip("Validation script not found; T035 implementation pending.")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=str(project_root)
    )
    return result

def test_pipeline_execution_success(pipeline_output):
    """
    Asserts that the quickstart validation script exits with code 0.
    """
    assert pipeline_output.returncode == 0, (
        f"Pipeline failed with exit code {pipeline_output.returncode}.\n"
        f"STDOUT:\n{pipeline_output.stdout}\n"
        f"STDERR:\n{pipeline_output.stderr}"
    )

def test_artifacts_exist(pipeline_output):
    """
    Asserts that all critical artifacts defined in T035 validation exist.
    """
    # Ensure we have a clean run first (handled by fixture)
    if pipeline_output.returncode != 0:
        pytest.skip("Pipeline execution failed, cannot check artifacts.")

    artifacts = [
        "data/derived/metadata_mpd.parquet",
        "data/derived/yearly_similarity.csv",
        "figures/similarity_trend.png",
        "figures/genre_similarity_heatmap.html",
        "data/derived/regression_results.json",
        "data/derived/cooks_distance_report.csv",
        "pipeline_log.txt"
    ]

    missing = []
    for artifact in artifacts:
        path = project_root / artifact
        if not path.exists():
            missing.append(artifact)

    assert len(missing) == 0, f"Missing artifacts: {missing}"

def test_log_contains_required_entries(pipeline_output):
    """
    Verifies that pipeline_log.txt contains key stage completion messages.
    """
    if pipeline_output.returncode != 0:
        pytest.skip("Pipeline execution failed.")

    log_path = project_root / "pipeline_log.txt"
    if not log_path.exists():
        pytest.fail("pipeline_log.txt not found.")

    content = log_path.read_text()
    required_entries = [
        "Ingestion complete",
        "Similarity calculation complete",
        "Regression fit complete"
    ]

    missing_entries = []
    for entry in required_entries:
        if entry not in content:
            missing_entries.append(entry)

    assert len(missing_entries) == 0, f"Log missing entries: {missing_entries}"
