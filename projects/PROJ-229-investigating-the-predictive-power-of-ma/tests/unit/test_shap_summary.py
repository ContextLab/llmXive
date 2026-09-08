"""
Unit test for the SHAP analysis script (T017d).

The test runs the script and verifies that the expected JSON file is created
and contains the required keys with matching lengths.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
def test_shap_summary_creation(tmp_path, monkeypatch):
    """
    Execute ``code/models/train_shap_analysis.py`` and assert that
    ``data/models/shap_summary.json`` is produced and has a sensible structure.
    """
    # Resolve the script location relative to the repository root.
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "code" / "models" / "train_shap_analysis.py"

    # Run the script in a subprocess to emulate real execution.
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    # The script should exit cleanly.
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Expected output file.
    output_path = repo_root / "data" / "models" / "shap_summary.json"
    assert output_path.is_file(), "shap_summary.json was not created"

    # Load and validate JSON content.
    with output_path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)

    # Basic schema checks.
    assert isinstance(payload, dict), "JSON root must be an object"
    assert "features" in payload, "Missing 'features' key"
    assert "mean_abs_shap" in payload, "Missing 'mean_abs_shap' key"

    features = payload["features"]
    shap_vals = payload["mean_abs_shap"]
    assert isinstance(features, list) and all(isinstance(f, str) for f in features)
    assert isinstance(shap_vals, list) and all(isinstance(v, (int, float)) for v in shap_vals)
    assert len(features) == len(shap_vals), "Feature and SHAP arrays must be same length"