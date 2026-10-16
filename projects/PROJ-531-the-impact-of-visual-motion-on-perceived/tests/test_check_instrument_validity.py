import json
import subprocess
from pathlib import Path

import pytest

@pytest.fixture
def download_status_path(tmp_path):
    """
    Creates a temporary ``data/raw/download_status.json`` file for testing.
    The fixture returns the path to the file.
    """
    data_raw = Path("data/raw")
    data_raw.mkdir(parents=True, exist_ok=True)
    status_file = data_raw / "download_status.json"
    yield status_file
    # Cleanup after test
    if status_file.is_file():
        status_file.unlink()

def test_invalid_instrument_exits_with_error(download_status_path):
    """
    When ``instrument_valid`` is false the script must exit with status code 1.
    """
    # Write a status file indicating an invalid instrument.
    download_status_path.write_text(
        json.dumps({"instrument_valid": False, "status": "unavailable"})
    )

    result = subprocess.run(
        ["python", "code/check_instrument_validity.py"],
        capture_output=True,
        text=True,
    )

    # The script should exit with code 1 and log an error message.
    assert result.returncode == 1
    assert "Instrument validation failed" in result.stderr or "Instrument validation failed" in result.stdout

def test_valid_instrument_exits_successfully(download_status_path):
    """
    When ``instrument_valid`` is true the script must exit with status code 0.
    """
    download_status_path.write_text(
        json.dumps({"instrument_valid": True, "status": "success"})
    )

    result = subprocess.run(
        ["python", "code/check_instrument_validity.py"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Instrument validation passed" in result.stderr or "Instrument validation passed" in result.stdout