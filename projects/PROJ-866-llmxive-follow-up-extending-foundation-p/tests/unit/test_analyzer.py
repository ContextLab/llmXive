"""
Unit tests for the analyzer (T007).

The tests verify that the analyzer script produces the two required
artefacts and that they conform to the expected contracts.
"""
import json
from pathlib import Path

from llmxive_toolkit import paths

# Import the entry point directly
from code.services.analyzer import run_analysis

def test_analyzer_produces_outputs(tmp_path: Path):
    # Redirect the project data directories to a temporary location
    # by monkey‑patching the llmxive_toolkit paths helpers.
    # The helpers create directories under the project root, so we
    # temporarily change the working directory.
    import os
    orig_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)

        # Copy a minimal step_outcomes.json into the expected location
        data_processed = paths.data("processed")
        data_processed.mkdir(parents=True, exist_ok=True)
        step_outcomes_src = Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "step_outcomes.json"
        step_outcomes_dest = data_processed / "step_outcomes.json"
        step_outcomes_dest.write_text(step_outcomes_src.read_text(encoding="utf-8"))

        # Run the analysis
        run_analysis()

        # Verify JSON output exists and contains required keys
        analysis_json = paths.results("analysis_results.json")
        assert analysis_json.is_file(), "analysis_results.json not created"
        with analysis_json.open("r", encoding="utf-8") as f:
            analysis_data = json.load(f)

        for key in ("threshold_pct", "ci_lower", "ci_upper", "regression_coefficients", "p_values", "n_samples"):
            assert key in analysis_data, f"Missing key {key} in analysis_results.json"

        # Verify CSV output exists and has at least three distinct compression_ratio values
        tradeoff_csv = paths.results("tradeoff_curve.csv")
        assert tradeoff_csv.is_file(), "tradeoff_curve.csv not created"
        import csv
        with tradeoff_csv.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) > 0, "CSV is empty"
        ratios = {float(r["compression_ratio"]) for r in rows}
        assert len(ratios) >= 3, "CSV must contain at least three distinct compression_ratio points"
    finally:
        os.chdir(orig_cwd)