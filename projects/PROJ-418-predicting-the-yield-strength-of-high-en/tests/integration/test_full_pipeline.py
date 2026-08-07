"""
Integration test for T117 – full pipeline execution.

The test runs the ``run_full_pipeline_exec.py`` script in a subprocess and
asserts that all mandatory output artefacts have been created.
"""

import subprocess
import sys
import pathlib
import json

# List of artefacts that must exist after a successful run.
REQUIRED_ARTIFACTS = [
    "output/manifest.json",
    "output/report.md",
    "output/metrics.json",
    "output/pipeline_runtime.json",
    "output/data_status.json",
    "data/processed/hea_descriptors.csv",
]


def test_full_pipeline_execution(tmp_path):
    """
    Execute the full pipeline and verify required artefacts.
    """
    # Run the pipeline script.  ``cwd`` is the repository root (the test is
    # executed from there by the verification harness).
    result = subprocess.run(
        [sys.executable, "code/run_full_pipeline_exec.py"],
        cwd=pathlib.Path.cwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # The pipeline must exit cleanly.
    assert result.returncode == 0, f"Pipeline failed: {result.stderr}"

    # Verify each required artefact exists and is non‑empty.
    for rel_path in REQUIRED_ARTIFACTS:
        path = pathlib.Path(rel_path)
        assert path.is_file(), f"Missing artefact: {rel_path}"
        assert path.stat().st_size > 0, f"Empty artefact: {rel_path}"

    # Additional sanity checks on JSON artefacts.
    manifest_path = pathlib.Path("output/manifest.json")
    manifest = json.loads(manifest_path.read_text())
    # The manifest must contain at least the provenance fields required by T047.
    for key in ("seeds", "hyperparameters", "library_versions", "timestamps", "checksums"):
        assert key in manifest, f"Manifest missing required field: {key}"

    metrics_path = pathlib.Path("output/metrics.json")
    metrics = json.loads(metrics_path.read_text())
    # Ensure both model entries are present.
    for model_key in ("rf", "linear"):
        assert model_key in metrics, f"Metrics missing model entry: {model_key}"
    # Verify that a best_model key exists and points to one of the models.
    assert metrics.get("best_model") in ("rf", "linear"), "Invalid best_model value"

    # Confirm that the runtime JSON reports a passing status.
    runtime_path = pathlib.Path("output/pipeline_runtime.json")
    runtime = json.loads(runtime_path.read_text())
    assert runtime.get("status") == "pass", "Pipeline runtime status not 'pass'"

    # Ensure the report contains the mandatory disclaimer (injected by T029b).
    report_path = pathlib.Path("output/report.md")
    report_text = report_path.read_text()
    disclaimer = "Associational analysis only; no causal inference"
    assert disclaimer in report_text, "Report missing mandatory disclaimer"