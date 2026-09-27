"""
Integration test for the full pipeline execution (task T117).

The test simply runs the ``code/execute_full_pipeline.py`` script and
checks that the five required output artifacts are present after the
run completes.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.fixture(scope="session")
def run_pipeline():
    """Execute the full pipeline once for the whole test session."""
    script = Path("code/execute_full_pipeline.py")
    assert script.is_file(), "Pipeline script missing"
    result = subprocess.run(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(
            f"Full pipeline execution failed (exit {result.returncode})\\n"
            f"STDOUT:\\n{result.stdout}\\nSTDERR:\\n{result.stderr}"
        )
    yield

def test_artifacts_exist(run_pipeline):
    """All required artifacts must exist after the pipeline run."""
    required_files = [
        Path("output/manifest.json"),
        Path("output/report.md"),
        Path("output/metrics.json"),
        Path("output/stability_rankings.json"),
        Path("output/external_metrics.json"),
    ]
    missing = [p for p in required_files if not p.is_file()]
    assert not missing, f"Missing expected pipeline artifacts: {missing}"

    # Basic sanity check that JSON files are well‑formed
    for json_file in [
        Path("output/manifest.json"),
        Path("output/metrics.json"),
        Path("output/stability_rankings.json"),
        Path("output/external_metrics.json"),
    ]:
        with json_file.open("r", encoding="utf-8") as f:
            try:
                json.load(f)
            except json.JSONDecodeError as exc:
                pytest.fail(f"Invalid JSON in {json_file}: {exc}")