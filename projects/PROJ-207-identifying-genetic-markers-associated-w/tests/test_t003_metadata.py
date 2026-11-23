"""Tests for T003: NCBI metadata download (code/01_download_metadata.py)."""
import json
import hashlib
from pathlib import Path

import pytest

METADATA = Path("data/processed/ncbi_metadata.json")
CHECKSUM = Path("data/processed/ncbi_metadata_checksum.txt")
LOG = Path("data/processed/ncbi_fetch_log.json")


def test_script_compiles():
    import py_compile
    py_compile.compile("code/01_download_metadata.py", doraise=True)


@pytest.mark.skipif(not METADATA.exists(), reason="metadata not yet downloaded")
def test_metadata_json_wellformed_and_count():
    data = json.loads(METADATA.read_text())
    assert data["sample_count"] >= 80
    assert len(data["samples"]) == data["sample_count"]
    required = {"sample_accession", "ccd_status", "varroa_load",
                "geographic_region", "sampling_year"}
    for s in data["samples"][:20]:
        assert required.issubset(s.keys())


@pytest.mark.skipif(not CHECKSUM.exists(), reason="checksum not yet written")
def test_checksum_matches():
    stored = CHECKSUM.read_text().split()[0]
    computed = hashlib.sha256(METADATA.read_bytes()).hexdigest()
    assert stored == computed


@pytest.mark.skipif(not LOG.exists(), reason="fetch log not yet written")
def test_fetch_log():
    log = json.loads(LOG.read_text())
    assert log["total_samples"] >= 80