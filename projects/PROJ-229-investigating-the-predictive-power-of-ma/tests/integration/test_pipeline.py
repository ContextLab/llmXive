"""
Integration test for the full data pipeline.

This test invokes the project's main pipeline entry point and verifies that
the key artifacts produced by the pipeline exist on disk. It is deliberately
lightweight and does not assert numerical correctness – those checks are
covered by unit and contract tests elsewhere – but it ensures that the
end‑to‑end workflow completes without raising exceptions and writes the
expected files.
"""

import pytest
from pathlib import Path

# The pipeline writes files relative to the repository root.  By changing the
# working directory to the repository root we guarantee that all relative
# paths used by the pipeline resolve correctly.
@pytest.fixture(autouse=True)
def change_to_repo_root(monkeypatch):
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.chdir(repo_root)
    yield

def test_data_pipeline_runs_successfully():
    """
    Run the pipeline and assert that the primary output files are present.
    """
    # Import the pipeline runner.  The import is performed after the cwd
    # change so that any relative‑path logic inside the module works as
    # intended.
    from code.main import run_pipeline

    # Execute the full pipeline.  Any exception will cause the test to fail.
    run_pipeline()

    # List of files that the pipeline is expected to generate.  These are
    # produced by the fetch, descriptor, and target‑decision stages.
    repo_root = Path(__file__).resolve().parents[2]
    expected_files = [
        repo_root / "data" / "raw" / "materials_project_data.json",
        repo_root / "data" / "raw" / "nist_data.json",
        repo_root / "data" / "processed" / "graph_features.npy",
        repo_root / "data" / "results" / "target_decision.json",
    ]

    missing = [str(p) for p in expected_files if not p.is_file()]
    assert not missing, f"Missing expected pipeline output files: {missing}"