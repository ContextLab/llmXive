"""
test_fetch_real_fail.py
-----------------------
Unit tests for T044: fetch_real.py fail-loudly behavior.

Verifies:
1. If plan.md has a URL but download fails -> raises exception.
2. If plan.md has NO URL -> returns "no_url" status (exit 0).
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add code root to path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from ingestion.fetch_real import main, _extract_url_from_plan, ensure_output_dir
from utils.config import get_project_root

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create necessary subdirectories
        (tmp_path / "data" / "raw").mkdir(parents=True)
        (tmp_path / "data" / "processed").mkdir(parents=True)
        # Patch get_project_root to return this temp dir
        with patch('utils.config.get_project_root', return_value=tmp_path):
            with patch('ingestion.fetch_real.get_project_root', return_value=tmp_path):
                yield tmp_path

def test_no_url_returns_no_status(temp_project_root):
    """
    Scenario: plan.md exists but has NO 'Dataset URL:' line.
    Expected: Script exits with code 0 and prints 'STATUS: no_url'.
    """
    # Create a plan.md without a URL
    plan_file = temp_project_root / "plan.md"
    plan_file.write_text("# Project Plan\n\nSome other content.\n")

    # Mock urlopen to prevent actual network call, though we expect early exit
    with patch('urllib.request.urlopen') as mock_urlopen:
        # We expect the script to exit before trying to download
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        # Verify no download was attempted
        mock_urlopen.assert_not_called()

def test_url_present_download_fails_raises(temp_project_root):
    """
    Scenario: plan.md has a URL, but download fails.
    Expected: Script raises FileNotFoundError/ConnectionError.
    """
    fake_url = "https://example.com/fake_data.csv"
    plan_file = temp_project_root / "plan.md"
    plan_file.write_text(f"# Project Plan\n\nDataset URL: {fake_url}\n")

    # Mock urlopen to raise a URLError
    with patch('urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = Exception("Network failure")

        # Also mock fetch_from_nist to return False
        with patch('ingestion.fetch_real.fetch_from_nist', return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                main()

            assert "Dataset download failed" in str(exc_info.value)

def test_url_present_download_succeeds(temp_project_root):
    """
    Scenario: plan.md has a URL, download succeeds.
    Expected: Script saves file, updates plan.md, exits 0.
    """
    fake_url = "https://example.com/real_data.csv"
    plan_file = temp_project_root / "plan.md"
    plan_file.write_text(f"# Project Plan\n\nDataset URL: {fake_url}\n")

    # Mock urlopen to return a fake response with CSV content
    mock_response = MagicMock()
    mock_response.read.side_effect = [b"smiles,solvent,diffusion\nC,water,1.0\n", b""]
    mock_response.__enter__ = lambda s: mock_response
    mock_response.__exit__ = lambda s, *args: None

    with patch('urllib.request.urlopen', return_value=mock_response):
        with patch('ingestion.fetch_real.fetch_from_nist', return_value=False):
            with patch('ingestion.fetch_real.log_info'):
                with patch('ingestion.fetch_real.log_error'):
                    # We expect exit 0 on success
                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 0
    
    # Verify file was created
    raw_dir = temp_project_root / "data" / "raw"
    assert (raw_dir / "dataset.csv").exists()
    
    # Verify plan.md was updated (or at least not changed incorrectly)
    content = plan_file.read_text()
    assert fake_url in content