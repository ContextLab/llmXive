"""Quick‑start integration test for T001.

The test invokes the ``code.run_pipeline`` module with the default
``--sample`` argument and verifies that the required artefacts are
created:

* ``data/generated/phi3-mini/sample_test.txt`` – the placeholder
  smoke‑test output.
* ``data/generated/generation_success_rates.csv`` – a CSV containing
  per‑model success‑rate columns.
* At least one intent‑entity JSON file under
  ``data/intermediate/intent_entities/`` (required by the contract test).
* A short log file ``logs/quickstart_run.log`` confirming the test run.
"""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from llmxive_toolkit import paths
from code import run_pipeline

@pytest.mark.parametrize("sample_arg", [None, ["--sample", "5"]])
def test_quickstart_creates_outputs(sample_arg):
    """Run the pipeline and check that the expected files exist."""
    # Build the argument list for the entry point.
    argv = sample_arg if sample_arg is not None else []
    # Execute the pipeline; a return code of 0 indicates success.
    exit_code = run_pipeline.main(argv)
    assert exit_code == 0, f"run_pipeline exited with non‑zero code {exit_code}"

    # 1. Smoke‑test placeholder output.
    smoke_path = paths.data("generated", "phi3-mini", "sample_test.txt")
    assert smoke_path.is_file(), f"Expected smoke‑test file {smoke_path} not found"

    # 2. Generation success‑rate CSV.
    csv_path = paths.data("generated", "generation_success_rates.csv")
    assert csv_path.is_file(), f"Expected CSV {csv_path} not found"

    # Verify CSV has the required columns and at least one row per model.
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows, "CSV is empty"
    expected_models = {"phi3-mini", "gemma2-2b", "llama3.2-3b"}
    csv_models = {row["model_id"] for row in rows}
    assert expected_models == csv_models, f"CSV models {csv_models} do not match expected {expected_models}"

    # 3. At least one intent‑entity JSON file.
    intent_dir = paths.data("intermediate", "intent_entities")
    json_files = list(intent_dir.glob("*.json"))
    assert json_files, f"No intent JSON files found in {intent_dir}"

    # 4. Write a short log file confirming the test run.
    log_path = paths.logs("quickstart_run.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("Quickstart integration test completed successfully.\n", encoding="utf-8")
