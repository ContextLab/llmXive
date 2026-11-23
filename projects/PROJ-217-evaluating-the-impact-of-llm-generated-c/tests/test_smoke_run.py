"""
Test that the smoke script produces the expected output file.
"""

import json
from pathlib import Path

from llmxive_toolkit import paths
from scripts.run_smoke import main as smoke_main


def test_smoke_produces_output(tmp_path, monkeypatch):
    """
    Run the smoke script in an isolated temporary directory and verify that
    data/results/smoke_analysis.json is created and contains the required keys.
    """
    # Redirect the toolkit paths to the temporary directory.
    monkeypatch.setattr("llmxive_toolkit.paths.root", tmp_path, raising=False)

    # Execute the smoke pipeline.
    smoke_main()

    # Verify the output file exists.
    output_path = paths.data("results", "smoke_analysis.json")
    assert output_path.is_file(), f"Missing expected file: {output_path}"

    # Load and validate the JSON structure.
    with output_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    assert "anova_time" in data, "anova_time section missing"
    for field in ("F", "p_value", "df_between", "df_within", "reject_null"):
        assert field in data["anova_time"], f"Missing {field} in anova_time"

    assert "anova_accuracy" in data, "anova_accuracy section missing"
    for field in ("F", "p_value", "df_between", "df_within", "reject_null"):
        assert field in data["anova_accuracy"], f"Missing {field} in anova_accuracy"