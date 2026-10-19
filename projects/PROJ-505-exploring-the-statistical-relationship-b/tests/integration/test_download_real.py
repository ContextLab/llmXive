"""
Integration tests for real-data ingestion (T003).

- Checksum computation is verified against a known SHA-256 digest.
- Fetch failures propagate loudly (ConnectionError/RuntimeError) and
  never fall back to synthetic data (fully offline, monkeypatched).
- Parse/checksum assertions run against the cached raw CDF files
  under data/raw/ and are SKIPPED when the cache is empty on a fresh
  offline runner.
"""
import pytest
import yaml
from pathlib import Path
from unittest.mock import patch

from llmxive_toolkit import paths
import code.ingestion.download_real as dr


def test_checksum_calculation():
    """Test that SHA-256 checksums are computed correctly."""
    test_file = paths.data("raw", "test_checksum.txt")
    test_file.write_text("hello world")
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert dr.compute_sha256(test_file) == expected
    test_file.unlink()


def test_fetch_failure_raises_loudly():
    """Verify that fetch failures raise ConnectionError/RuntimeError and never fall back."""
    with patch("pyspedas.cdaweb.cdaweb") as mock_cdaweb:
        mock_cdaweb.side_effect = Exception("CDAWeb Timeout")
        with pytest.raises((ConnectionError, RuntimeError)):
            dr.download_and_preserve(start="2000-01-01", end="2000-01-02")


def _raw_cdfs():
    raw_root = paths.data("raw")
    return sorted(raw_root.rglob("*.cdf"))


def test_raw_files_and_checksums_exist():
    """
    Assert that raw CDF files exist for ACE SWICS, WIND SMS, and OMNI,
    and that checksums.yaml matches the files on disk.
    Skips when the cache is empty (fresh offline runner).
    """
    cdfs = _raw_cdfs()
    if not cdfs:
        pytest.skip("No raw CDF files cached under data/raw/. Run code/ingestion/download_real.py first.")

    raw_root = paths.data("raw")
    for sub in ("ace_swics", "wind_sms", "omni"):
        assert (raw_root / sub).exists(), f"missing data/raw/{sub}/"
        assert any((raw_root / sub).rglob("*.cdf")), f"no raw CDF files in data/raw/{sub}/"

    checksum_path = raw_root / "checksums.yaml"
    assert checksum_path.exists()

    with open(checksum_path, "r") as f:
        checksums = yaml.safe_load(f)

    assert isinstance(checksums, dict)
    assert len(checksums) > 0

    # Verify every checksummed file exists and its digest matches
    for rel_path, digest in checksums.items():
        p = raw_root / rel_path
        assert p.exists(), f"checksummed file missing: {rel_path}"
        assert dr.compute_sha256(p) == digest, f"checksum mismatch for {rel_path}"


def test_parsed_columns_include_species_and_indices():
    """
    Parse cached raw CDFs and assert the composition species (ACE
    SWICS) and the Dst/Kp indices (OMNI) are present.
    Skips when the cache is empty (fresh offline runner).
    """
    cdfs = _raw_cdfs()
    if not cdfs:
        pytest.skip("No raw CDF files cached under data/raw/. Run code/ingestion/download_real.py first.")

    from cdflib import CDF

    raw_root = paths.data("raw")

    omni_cdfs = sorted((raw_root / "omni").rglob("*.cdf"))
    assert omni_cdfs, "no OMNI CDF cached"
    omni_vars = CDF(str(omni_cdfs[0])).cdf_info().zVariables
    omni_upper = [v.upper() for v in omni_vars]
    assert any("DST" in v for v in omni_upper), f"Dst index variable not found in OMNI CDF: {omni_vars}"
    assert any(v.startswith("KP") for v in omni_upper), f"Kp index variable not found in OMNI CDF: {omni_vars}"

    ace_cdfs = sorted((raw_root / "ace_swics").rglob("*.cdf"))
    assert ace_cdfs, "no ACE SWICS CDF cached"
    ace_vars = CDF(str(ace_cdfs[0])).cdf_info().zVariables
    joined = " ".join(ace_vars).upper()
    for species in ("H", "HE", "C", "O", "FE"):
        assert species in joined, f"composition species '{species}' not found in ACE SWICS CDF: {ace_vars}"

    wind_cdfs = sorted((raw_root / "wind_sms").rglob("*.cdf"))
    assert wind_cdfs, "no WIND SMS CDF cached"