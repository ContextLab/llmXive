"""
Unit tests for the GTFS fetcher.
"""
import os
import tempfile
import zipfile
from pathlib import Path
import pytest
import sys

# Add src to path if running standalone, though the project structure usually handles this
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.lib.gtfs_fetcher import fetch_gtfs_feed, compute_sha256

def test_fetch_gtfs_creates_file():
    """
    Test that fetch_gtfs_feed successfully downloads the file and saves it.
    Note: This test attempts a real network request. If the network is down or 
    the MTA feed is unreachable, this test will fail, which is expected behavior
    for this task's constraint ("fails if canonical source unreachable").
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        try:
            result_path = fetch_gtfs_feed(output_dir=output_dir)
            
            # Verify file exists
            assert result_path.exists(), "Downloaded file does not exist"
            
            # Verify it is a zip
            assert zipfile.is_zipfile(result_path), "Downloaded file is not a valid zip"
            
            # Verify content
            with zipfile.ZipFile(result_path, 'r') as zf:
                names = zf.namelist()
                stops_found = any("stops.txt" in n for n in names)
                assert stops_found, "GTFS archive missing stops.txt"
                
        except RuntimeError as e:
            # If the canonical source is unreachable, the function raises RuntimeError.
            # In a CI environment without internet or if MTA is down, this is a valid failure mode
            # for the fetcher, but for the test to pass in a "happy path" scenario, we assume connectivity.
            # However, per task instructions: "fails if canonical source unreachable".
            # We re-raise to indicate the fetcher is working as intended (failing loudly).
            pytest.fail(f"GTFS fetcher failed to reach canonical source: {e}")

def test_fetch_gtfs_invalid_url():
    """
    Test that fetch_gtfs_feed raises RuntimeError for an invalid URL.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        invalid_url = "https://this-domain-definitely-does-not-exist-12345.com/gtfs.zip"
        
        with pytest.raises(RuntimeError) as excinfo:
            fetch_gtfs_feed(output_dir=output_dir, url=invalid_url)
        
        assert "canonical source" in str(excinfo.value).lower() or "Network Error" in str(excinfo.value)

def test_compute_sha256():
    """
    Test the SHA256 computation function.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Hello, World!")
        
        hash1 = compute_sha256(test_file)
        hash2 = compute_sha256(test_file)
        
        assert len(hash1) == 64  # SHA256 hex length
        assert hash1 == hash2
        
        # Known hash for "Hello, World!"
        # e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 is empty string
        # 315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3 is "Hello, World!"
        assert hash1 == "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"