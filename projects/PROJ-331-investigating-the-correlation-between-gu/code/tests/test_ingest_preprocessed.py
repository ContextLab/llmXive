"""Tests for the ingest module's preprocessed validation.

This test creates minimal synthetic raw input files that satisfy the
required schema and verifies that ``ingest.validate_inputs`` succeeds
and reports the correct flags.

The synthetic data is generated on‑the‑fly within the test and does
not constitute real study data; it is only used to exercise the
validation logic.
"""

from pathlib import Path

import pandas as pd
import pytest

# Import the module under test.
from src.pipeline import ingest

@pytest.fixture
def temp_raw_files(tmp_path: Path):
    """Create temporary ASV CSV and clinical Parquet files with required columns."""
    # ASV table
    asv_path = tmp_path / "open_asv.csv"
    asv_df = pd.DataFrame(
        {
            "sample_id": ["S1", "S2"],
            "patient_id": ["P1", "P1"],
            "visit_date": ["2021-01-01", "2021-06-01"],
            # Minimal taxon column
            "taxon_X": [10, 15],
            "preprocessed": [True, True],
        }
    )
    asv_df.to_csv(asv_path, index=False)

    # Clinical metadata
    clinical_path = tmp_path / "open_clinical.parquet"
    clinical_df = pd.DataFrame(
        {
            "patient_id": ["P1", "P1"],
            "visit_date": ["2021-01-01", "2021-06-01"],
            "age": [65, 66],
            "sex": ["M", "M"],
            "levodopa_eq_dose": [300, 310],
            "MDS_UPDRS_Total": [20, 25],
        }
    )
    clinical_df.to_parquet(clinical_path)

    return asv_path, clinical_path

def test_validate_inputs_success(temp_raw_files):
    """The ingest module should accept valid files and report no skip flags."""
    asv_path, clinical_path = temp_raw_files

    report = ingest.validate_inputs(asv_path=asv_path, clinical_path=clinical_path)

    # Basic sanity checks on the report contents.
    assert report["asv_path"] == str(asv_path)
    assert report["clinical_path"] == str(clinical_path)
    assert report["outcome_column_present"] is True
    assert report["skip_slope_and_correlation"] is False
    assert report["skip_mixed_effects"] is False
    # Checksums are computed – they should be non‑empty strings.
    assert isinstance(report["asv_checksum_sha256"], str) and len(report["asv_checksum_sha256"]) == 64
    assert isinstance(report["clinical_checksum_sha256"], str) and len(report["clinical_checksum_sha256"]) == 64

def test_validate_inputs_missing_preprocessed_flag(tmp_path: Path):
    """If the ``preprocessed`` column is missing, validation must fail."""
    # Create an ASV file without the required provenance column.
    asv_path = tmp_path / "open_asv.csv"
    asv_df = pd.DataFrame(
        {
            "sample_id": ["S1"],
            "patient_id": ["P1"],
            "visit_date": ["2021-01-01"],
            "taxon_X": [10],
            # Note: no ``preprocessed`` column.
        }
    )
    asv_df.to_csv(asv_path, index=False)

    # Minimal clinical file (valid).
    clinical_path = tmp_path / "open_clinical.parquet"
    clinical_df = pd.DataFrame(
        {
            "patient_id": ["P1"],
            "visit_date": ["2021-01-01"],
            "age": [65],
            "sex": ["M"],
            "levodopa_eq_dose": [300],
            "MDS_UPDRS_Total": [20],
        }
    )
    clinical_df.to_parquet(clinical_path)

    # The validation should raise a FileNotFoundError (via _fail) because the
    # provenance column is missing.
    with pytest.raises(FileNotFoundError) as excinfo:
        ingest.validate_inputs(asv_path=asv_path, clinical_path=clinical_path)
    assert "required provenance column 'preprocessed' is missing" in str(excinfo.value)

def test_validate_inputs_preprocessed_false(tmp_path: Path):
    """Rows where ``preprocessed`` is not True must cause validation to fail."""
    asv_path = tmp_path / "open_asv.csv"
    asv_df = pd.DataFrame(
        {
            "sample_id": ["S1"],
            "patient_id": ["P1"],
            "visit_date": ["2021-01-01"],
            "taxon_X": [10],
            "preprocessed": [False],  # Invalid flag.
        }
    )
    asv_df.to_csv(asv_path, index=False)

    clinical_path = tmp_path / "open_clinical.parquet"
    clinical_df = pd.DataFrame(
        {
            "patient_id": ["P1"],
            "visit_date": ["2021-01-01"],
            "age": [65],
            "sex": ["M"],
            "levodopa_eq_dose": [300],
            "MDS_UPDRS_Total": [20],
        }
    )
    clinical_df.to_parquet(clinical_path)

    with pytest.raises(FileNotFoundError) as excinfo:
        ingest.validate_inputs(asv_path=asv_path, clinical_path=clinical_path)
    assert "Provenance check failed" in str(excinfo.value) and "must be True for all rows" in str(excinfo.value)