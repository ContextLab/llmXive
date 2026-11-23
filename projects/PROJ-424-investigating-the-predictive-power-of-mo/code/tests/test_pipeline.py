"""
Integration test for the end‑to‑end pipeline.

This test runs the pipeline for a minimal configuration (water, 1 ns, seed 0)
and checks that:
  * a CSV file is created at the expected location,
  * the CSV contains exactly one data row (plus header),
  * the row validates against the diffusion_results JSON schema.
"""

import csv
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError

from code.pipeline import run_pipeline
from llmxive_toolkit import paths

@pytest.fixture(scope="module")
def csv_path():
    # Ensure a clean state before the test runs
    p = paths.data("processed", "diffusion_results.csv")
    if p.exists():
        p.unlink()
    yield p
    # Cleanup after test
    if p.exists():
        p.unlink()

def test_end_to_end_pipeline(csv_path: Path):
    # Execute the pipeline
    result = run_pipeline(solvent="water", duration_ns=1.0, seed=0)

    # Verify the CSV file exists
    assert csv_path.is_file(), "diffusion_results.csv was not created"

    # Read the CSV and check row count (header + one data row)
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1, f"Expected exactly one result row, found {len(rows)}"

    # Validate the row against the JSON schema
    schema_path = paths.code("..", "contracts", "diffusion_results.schema.yaml")
    with schema_path.open() as sf:
        schema = json.load(sf)

    row = rows[0]
    # Cast numeric fields to float for validation (mirrors pipeline internal logic)
    numeric_fields = {
        "timescale_ns",
        "msd_r_squared",
        "diffusion_coefficient",
        "scaled_diffusion_coefficient",
        "nist_reference",
        "mae",
    }
    for k in numeric_fields:
        row[k] = float(row[k])

    # Should not raise ValidationError
    try:
        validate(instance=row, schema=schema)
    except ValidationError as e:
        pytest.fail(f"CSV row failed schema validation: {e.message}")