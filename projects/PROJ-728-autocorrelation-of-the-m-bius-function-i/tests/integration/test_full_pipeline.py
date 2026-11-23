"""
Integration test for the full Möbius autocorrelation pipeline.

The test invokes ``python -m code.main`` as a subprocess and then
checks that the expected final artefacts exist on disk.
"""

import pathlib
import subprocess
import sys

import pytest


@pytest.mark.timeout(600)
def test_full_pipeline_runs_successfully(tmp_path: pathlib.Path, monkeypatch):
    """
    Run the master pipeline and verify the presence of the final outputs.

    The test uses the repository's working directory; no temporary
    directory manipulation is required because the pipeline writes to
    fixed locations under the project root.
    """
    # Ensure we are executing from the project root.
    project_root = pathlib.Path(__file__).resolve().parents[2]
    monkeypatch.chdir(project_root)

    # Run the pipeline.
    result = subprocess.run(
        [sys.executable, "-m", "code.main"],
        capture_output=True,
        text=True,
    )
    # The pipeline should exit with status 0.
    assert result.returncode == 0, (
        f"Pipeline failed (exit {result.returncode}). "
        f"stdout: {result.stdout}\\nstderr: {result.stderr}"
    )

    # Expected artefacts.
    expected_files = [
        pathlib.Path("data/processed/autocorr_stats.csv"),
        pathlib.Path("outputs/figures/heatmap_L1000.png"),
        pathlib.Path("outputs/figures/heatmap_L10000.png"),
        pathlib.Path("outputs/figures/heatmap_L100000.png"),
        pathlib.Path("data/processed/uniformity_test.json"),
    ]

    for f in expected_files:
        assert f.is_file(), f"Expected file not found: {f}"