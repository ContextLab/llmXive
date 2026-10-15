import json
import pytest
from pathlib import Path

from verify_data_source import main as verify_main

def test_verify_fails_when_no_external_dataset(tmp_path, monkeypatch):
    """
    Ensure that the script raises RuntimeError when no external dataset
    can be discovered. We monkey‑patch the discovery function to return
    an empty list, forcing the failure path.
    """
    # Patch the internal discovery function
    from verify_data_source import _discover_external_datasets

    def fake_discover():
        return []

    monkeypatch.setattr("verify_data_source._discover_external_datasets", fake_discover)

    # Run and expect RuntimeError
    with pytest.raises(RuntimeError):
        verify_main()

    # No report should be written
    report_path = Path(__file__).parents[2] / "data" / "source" / "availability_report.json"
    assert not report_path.exists()