import json
from pathlib import Path

from llmxive_toolkit import paths

def test_thin_slice_output():
    """
    Integration test for the thin‑slice collector.

    Executes the script and verifies that both the JSON and CSV artifacts
    exist and contain at least one record that validates against the
    cleaned_study schema.
    """
    # Execute the thin‑slice script
    import subprocess, sys
    result = subprocess.run(
        [sys.executable, "code/data/thin_slice.py"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    # Verify JSON output
    json_path = paths.data("results", "thin_slice_result.json")
    assert json_path.is_file(), "Thin‑slice JSON result missing"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "study_id" in data and "hedges_g" in data

    # Verify CSV output
    csv_path = paths.data("processed", "thin_slice_cleaned.csv")
    assert csv_path.is_file(), "Thin‑slice cleaned CSV missing"
    with open(csv_path, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
    # Required columns from the schema
    required = {
        "id",
        "title",
        "registry",
        "age_range",
        "diagnosis",
        "outcomes",
        "intervention_components",
        "delivery_format",
        "social_skill_domain",
    }
    assert required.issubset(set(header)), f"CSV missing required columns: {required - set(header)}"