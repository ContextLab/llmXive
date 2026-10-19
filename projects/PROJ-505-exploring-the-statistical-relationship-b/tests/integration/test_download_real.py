import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
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
    with patch("pyspedas.omni") as mock_omni:
        mock_omni.side_effect = Exception("CDAWeb Timeout")
        with pytest.raises((ConnectionError, RuntimeError)):
            dr.download_and_preserve()

def test_raw_files_and_checksums_exist():
    """
    Assert that raw files exist for ACE, WIND, and OMNI, and checksums are written.
    Skips if the data hasn't been downloaded yet (fresh offline runner).
    """
    # Check if any CDF or data files exist in the raw directory
    raw_root = paths.data("raw")
    has_data = any(raw_root.rglob("*"))
    
    if not has_data:
        pytest.skip("No raw data found in data/raw/. Run download_real.py first.")

    # Verify directories
    assert (raw_root / "ace_swics").exists()
    assert (raw_root / "wind_sms").exists()
    assert (raw_root / "omni").exists()

    # Verify checksums file
    checksum_path = raw_root / "checksums.yaml"
    assert checksum_path.exists()
    
    with open(checksum_path, "r") as f:
        checksums = yaml.safe_load(f)
    
    assert isinstance(checksums, dict)
    assert len(checksums) > 0
    
    # Verify a random file from checksums actually exists
    sample_rel_path = list(checksums.keys())[0]
    assert (raw_root / sample_rel_path).exists()