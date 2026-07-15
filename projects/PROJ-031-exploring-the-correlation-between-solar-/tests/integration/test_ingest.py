"""
Integration tests for the ingest module.
These tests verify that the ingestion logic handles real data structures correctly.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import io

# Import the module to test
import sys
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from ingest import fetch_goes_flares, write_goes_flare_data, main
from datetime import datetime


@pytest.fixture
def mock_ftp_response():
    """
    Mock data simulating the response from NOAA SWPC FTP.
    This mimics the actual format of goes-flare_list.txt.
    """
    # Simulated header and data lines
    header = "# Peak Time (UT) Class Location Start Time (UT) End Time (UT) ...\n"
    # Sample data rows (PeakTime, Class, Location, Start, End)
    data = [
        "20230101120000 M1.0 N12W45 20230101115500 20230101120500\n",
        "20230102083000 X2.5 S10E20 20230102082000 20230102084000\n",
        "20230103150000 C5.2 N20W10 20230103145000 20230103151000\n",
    ]
    return header + "".join(data)


@patch('ingest.ftplib.FTP')
def test_fetch_goes_flares_success(mock_ftp_class, mock_ftp_response):
    """
    Test successful retrieval and parsing of GOES flare data.
    """
    mock_ftp_instance = MagicMock()
    mock_ftp_class.return_value = mock_ftp_instance
    
    # Mock nlst to return a flare file
    mock_ftp_instance.nlst.return_value = ["/pub/lists/goes/goes-flare_list.txt"]
    
    # Mock retrlines to yield our simulated data
    def mock_retrlines(cmd, callback):
        lines = mock_ftp_response.splitlines()
        for line in lines:
            callback(line + "\n")
    
    mock_ftp_instance.retrlines.side_effect = mock_retrlines
    mock_ftp_instance.cwd.return_value = None

    # Execute
    events = fetch_goes_flares()

    # Assertions
    assert len(events) == 3, f"Expected 3 events, got {len(events)}"
    assert events[0]["class"] == "M1.0"
    assert "2023-01-01" in events[0]["peak_time"]
    assert events[0]["location"] == "N12W45"

    # Verify FTP calls
    mock_ftp_instance.login.assert_called_once()
    mock_ftp_instance.nlst.assert_called()


@patch('ingest.ftplib.FTP')
def test_fetch_goes_flares_connection_failure(mock_ftp_class):
    """
    Test that a connection error is raised when FTP is unreachable.
    """
    mock_ftp_class.side_effect = Exception("Connection Refused")

    with pytest.raises(ConnectionError):
        fetch_goes_flares()


@patch('ingest.ftplib.FTP')
def test_fetch_goes_flares_no_data(mock_ftp_class, caplog):
    """
    Test that a RuntimeError is raised if no flare files are found.
    """
    mock_ftp_instance = MagicMock()
    mock_ftp_class.return_value = mock_ftp_instance
    
    # No flare files found
    mock_ftp_instance.nlst.return_value = ["/pub/lists/other/file.txt"]

    with pytest.raises(RuntimeError, match="No flare list files found"):
        fetch_goes_flares()


def test_write_goes_flare_data(tmp_path):
    """
    Test writing events to CSV.
    """
    events = [
        {"peak_time": "2023-01-01T12:00:00", "class": "M1.0", "location": "N12W45"},
        {"peak_time": "2023-01-02T08:30:00", "class": "X2.5", "location": "S10E20"}
    ]
    
    output_file = tmp_path / "test_flares.csv"
    write_goes_flare_data(events, output_file)
    
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        content = f.read()
    
    assert "peak_time" in content
    assert "M1.0" in content
    assert "X2.5" in content