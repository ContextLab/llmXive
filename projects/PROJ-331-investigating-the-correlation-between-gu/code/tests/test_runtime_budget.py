"""Test that the pipeline records per‑stage runtimes and respects the
overall and permutation time budgets (SC‑003)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import pytest

# Import the pipeline entry point
from code.src.pipeline import __main__ as pipeline_main
from llmxive_toolkit import paths

@pytest.fixture
def tiny_dataset(tmp_path: Path):
    """Create a minimal, valid dataset and place it in the default raw locations."""
    # ASV CSV
    asv_rows = [
        {"sample_id": "s1", "patient_id": "p1", "visit_date": "2020-01-01", "taxon_a": 10, "taxon_b": 5},
        {"sample_id": "s2", "patient_id": "p1", "visit_date": "2021-01-01", "taxon_a": 12, "taxon_b": 6},
        {"sample_id": "s3", "patient_id": "p2", "visit_date": "2020-01-01", "taxon_a": 8, "taxon_b": 4},
        {"sample_id": "s4", "patient_id": "p2", "visit_date": "2021-01-01", "taxon_a": 9, "taxon_b": 5},
    ]
    asv_df = pd.DataFrame(asv_rows)
    asv_path = paths.data("raw", "ppmi_asv.csv")
    asv_path.parent.mkdir(parents=True, exist_ok=True)
    asv_df.to_csv(asv_path, index=False)

    # Clinical Parquet
    clin_rows = [
        {"patient_id": "p1", "visit_date": "2020-01-01", "age": 65, "sex": "M", "levodopa_eq_dose": 100, "MDS_UPDRS_Total": 30},
        {"patient_id": "p1", "visit_date": "2021-01-01", "age": 66, "sex": "M", "levodopa_eq_dose": 110, "MDS_UPDRS_Total": 35},
        {"patient_id": "p2", "visit_date": "2020-01-01", "age": 70, "sex": "F", "levodopa_eq_dose": 0,   "MDS_UPDRS_Total": 28},
        {"patient_id": "p2", "visit_date": "2021-01-01", "age": 71, "sex": "F", "levodopa_eq_dose": 10,  "MDS_UPDRS_Total": 32},
    ]
    clin_df = pd.DataFrame(clin_rows)
    clin_path = paths.data("raw", "ppmi_clinical.parquet")
    clin_path.parent.mkdir(parents=True, exist_ok=True)
    clin_df.to_parquet(clin_path, index=False)

    return asv_path, clin_path

def test_runtime_logging_and_budget(tmp_path: Path, monkeypatch):
    """Run the full pipeline on a tiny dataset and verify runtime logging."""
    # Redirect the project root to a temporary directory so we do not pollute the repository.
    monkeypatch.setattr(paths, "root", tmp_path, raising=False)

    # Ensure the runtime log does not exist before the run.
    runtime_log = paths.results("runtime_log.txt")
    if runtime_log.is_file():
        runtime_log.unlink()

    # Create the tiny dataset in the temporary project structure.
    # The fixture writes to paths.data which now points inside tmp_path.
    asv_path, clin_path = tiny_dataset(tmp_path)

    # Run the pipeline with a very small permutation count to keep the test fast.
    # We also limit taxa to 10 (more than enough for this tiny dataset).
    exit_code = pipeline_main.main(
        ["--seed", "42", "--max_taxa", "10", "--perm_iterations", "5"]
    )
    assert exit_code == 0

    # Verify that the runtime log file was created.
    assert runtime_log.is_file()

    # Load the log and check that each expected stage appears.
    log_text = runtime_log.read_text(encoding="utf-8")
    expected_stages = [
        "Ingest",
        "Preprocess",
        "Slope computation",
        "Correlation analysis",
        "Linear Mixed‑Effects modelling",
        "Permutation robustness test",
        "Total",
    ]
    for stage in expected_stages:
        assert stage in log_text, f"Stage '{stage}' missing from runtime log."

    # Parse the total elapsed time and assert it is well within the 6‑hour budget.
    total_line = [ln for ln in log_text.splitlines() if ln.startswith("Total:")][0]
    total_seconds = float(total_line.split(":")[1].strip().split()[0])
    assert total_seconds < 6 * 60 * 60, "Pipeline exceeded the 6‑hour total budget."

    # Parse the permutation elapsed time and assert it is within the 4‑hour budget.
    perm_line = [ln for ln in log_text.splitlines() if ln.startswith("Permutation robustness test:")][0]
    perm_seconds = float(perm_line.split(":")[1].strip().split()[0])
    assert perm_seconds < 4 * 60 * 60, "Permutation step exceeded the 4‑hour budget."

    # Clean up generated files (optional, pytest's tmp_path will be removed).