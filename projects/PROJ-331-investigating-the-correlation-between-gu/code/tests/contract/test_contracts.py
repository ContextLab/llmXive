"""Contract validation for the correlation results.

The contract schema lives at ``contracts/taxa_results.schema.yaml``.
This test loads the schema and validates each row of the generated
``taxa_correlations.csv`` against it using ``jsonschema``.
"""

from __future__ import annotations

import pathlib
import yaml
from jsonschema import Draft7Validator

import pandas as pd
import pytest

from code.src.pipeline import (
    ingest,
    preprocess,
    slopes,
    correlation,
)

@pytest.fixture
def synthetic_dataset(tmp_path: pathlib.Path):
    """Create a minimal synthetic dataset (same as in test_correlation)."""
    # ASV
    asv_rows = [
        {"sample_id": "s1", "patient_id": "p1", "visit_date": "2020-01-01", "taxon_a": 10, "taxon_b": 5},
        {"sample_id": "s2", "patient_id": "p1", "visit_date": "2021-01-01", "taxon_a": 12, "taxon_b": 6},
        {"sample_id": "s3", "patient_id": "p2", "visit_date": "2020-01-01", "taxon_a": 8, "taxon_b": 4},
        {"sample_id": "s4", "patient_id": "p2", "visit_date": "2021-01-01", "taxon_a": 9, "taxon_b": 5},
    ]
    asv_df = pd.DataFrame(asv_rows)
    asv_path = tmp_path / "ppmi_asv.csv"
    asv_df.to_csv(asv_path, index=False)

    # Clinical
    clin_rows = [
        {"patient_id": "p1", "visit_date": "2020-01-01", "age": 60, "sex": "M", "levodopa_eq_dose": 100, "MDS_UPDRS_Total": 30},
        {"patient_id": "p1", "visit_date": "2021-01-01", "age": 61, "sex": "M", "levodopa_eq_dose": 110, "MDS_UPDRS_Total": 35},
        {"patient_id": "p2", "visit_date": "2020-01-01", "age": 65, "sex": "F", "levodopa_eq_dose": 0,   "MDS_UPDRS_Total": 28},
        {"patient_id": "p2", "visit_date": "2021-01-01", "age": 66, "sex": "F", "levodopa_eq_dose": 10,  "MDS_UPDRS_Total": 32},
    ]
    clin_df = pd.DataFrame(clin_rows)
    clin_path = tmp_path / "ppmi_clinical.parquet"
    clin_df.to_parquet(clin_path, index=False)

    return asv_path, clin_path

def _run_full_pipeline(tmp_path: pathlib.Path, asv_path: pathlib.Path, clin_path: pathlib.Path):
    """Helper that runs ingest → preprocess → slopes → correlation."""
    ingest.main(asv_path, clin_path, tmp_path / "ingest_validation.json")

    processed_dir = tmp_path / "processed"
    preprocess.run_preprocess(
        asv_path,
        clin_path,
        out_dir=processed_dir,
        max_taxa=10,
    )

    taxon_slopes_path, outcome_slopes_path = slopes.run_slopes(
        processed_dir / "clr_abundances.parquet",
        clin_path,
    )

    results_path, _ = correlation.run_correlation(
        partial=False,
        taxon_slopes_path=taxon_slopes_path,
        outcome_slopes_path=outcome_slopes_path,
    )
    return results_path

def test_taxa_correlations_contract(tmp_path: pathlib.Path, synthetic_dataset):
    """Validate that the generated CSV conforms to the contract schema."""
    asv_path, clin_path = synthetic_dataset

    results_path = _run_full_pipeline(tmp_path, asv_path, clin_path)

    # Load the contract schema (YAML → dict)
    schema_path = pathlib.Path("contracts") / "taxa_results.schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    validator = Draft7Validator(schema)

    df = pd.read_csv(results_path)

    # Validate each row against the schema
    for _, row in df.iterrows():
        # Convert pandas Series to a plain dict with native Python types
        record = {k: (v.item() if hasattr(v, "item") else v) for k, v in row.items()}
        validator.validate(record)

    # If we reach this point without raising, the contract is satisfied.