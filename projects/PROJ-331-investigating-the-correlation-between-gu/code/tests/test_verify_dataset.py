"""Tests for the PPMI dataset verification script (T013)."""
from __future__ import annotations

import pathlib
import tempfile

import pandas as pd
import pytest
import requests

from code.src.pipeline import verify_dataset

# ----------------------------------------------------------------------
# Helper to create a minimal CSV and Parquet file and compute their digests.
# ----------------------------------------------------------------------
def _create_asv_file(tmp_dir: pathlib.Path, content: str) -> pathlib.Path:
    path = tmp_dir / "ppmi_asv.csv"
    path.write_text(content, encoding="utf-8")
    return path

def _create_clinical_file(tmp_dir: pathlib.Path) -> pathlib.Path:
    df = pd.DataFrame(
        {
            "patient_id": ["p1", "p2"],
            "visit_date": ["2020-01-01", "2020-06-01"],
            "age": [65, 70],
            "sex": ["M", "F"],
            "levodopa_eq_dose": [100, 0],
            "MDS_UPDRS_Total": [30, 28],
        }
    )
    path = tmp_dir / "ppmi_clinical.parquet"
    df.to_parquet(path, index=False)
    return path

def _sha256(path: pathlib.Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------
@pytest.fixture
def valid_dataset(tmp_path: pathlib.Path):
    """Create a pair of valid files and return their paths and digests."""
    asv_path = _create_asv_file(tmp_path, "sample_id,patient_id,visit_date,taxon_a\ns1,p1,2020-01-01,10\n")
    clinical_path = _create_clinical_file(tmp_path)
    return asv_path, clinical_path, _sha256(asv_path), _sha256(clinical_path)

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------
def test_successful_verification(monkeypatch, valid_dataset):
    """All checks pass when files exist, checksums match and citation is reachable."""
    asv_path, clinical_path, asv_hash, clinical_hash = valid_dataset

    # Monkey‑patch the expected digests used by the module.
    monkeypatch.setattr(verify_dataset, "EXPECTED_ASV_SHA256", asv_hash)
    monkeypatch.setattr(verify_dataset, "EXPECTED_CLINICAL_SHA256", clinical_hash)

    # Monkey‑patch the request to avoid real network traffic.
    class DummyResponse:
        status_code = 200

    monkeypatch.setattr(requests, "head", lambda *args, **kwargs: DummyResponse())

    # Should not raise.
    result = verify_dataset.verify_dataset(
        asv_path=asv_path,
        clinical_path=clinical_path,
        expected_asv=asv_hash,
        expected_clinical=clinical_hash,
    )
    assert result == (asv_path, clinical_path)

def test_missing_file_raises(monkeypatch, tmp_path):
    """FileNotFoundError is raised when either input file is absent."""
    asv_path = tmp_path / "nonexistent_asv.csv"
    clinical_path = tmp_path / "nonexistent_clinical.parquet"

    with pytest.raises(FileNotFoundError):
        verify_dataset.verify_dataset(
            asv_path=asv_path,
            clinical_path=clinical_path,
            expected_asv="dummy",
            expected_clinical="dummy",
        )

def test_checksum_mismatch_raises(monkeypatch, valid_dataset):
    """ValueError is raised when a checksum does not match the expected value."""
    asv_path, clinical_path, asv_hash, clinical_hash = valid_dataset

    # Intentionally supply a wrong checksum for the ASV file.
    wrong_hash = "0" * 64

    # Monkey‑patch citation check to always succeed.
    class DummyResponse:
        status_code = 200

    monkeypatch.setattr(requests, "head", lambda *args, **kwargs: DummyResponse())

    with pytest.raises(ValueError) as excinfo:
        verify_dataset.verify_dataset(
            asv_path=asv_path,
            clinical_path=clinical_path,
            expected_asv=wrong_hash,
            expected_clinical=clinical_hash,
        )
    assert "ASV file checksum mismatch" in str(excinfo.value)

def test_unreachable_citation_raises(monkeypatch, valid_dataset):
    """ConnectionError is raised when the citation URL cannot be reached."""
    asv_path, clinical_path, asv_hash, clinical_hash = valid_dataset

    # Monkey‑patch the checksum expectations to the correct values.
    monkeypatch.setattr(verify_dataset, "EXPECTED_ASV_SHA256", asv_hash)
    monkeypatch.setattr(verify_dataset, "EXPECTED_CLINICAL_SHA256", clinical_hash)

    # Simulate a failed HTTP request.
    def raise_conn(*args, **kwargs):
        raise requests.RequestException("network failure")

    monkeypatch.setattr(requests, "head", raise_conn)

    with pytest.raises(ConnectionError) as excinfo:
        verify_dataset.verify_dataset(
            asv_path=asv_path,
            clinical_path=clinical_path,
            expected_asv=asv_hash,
            expected_clinical=clinical_hash,
        )
    assert "Unable to reach citation URL" in str(excinfo.value)