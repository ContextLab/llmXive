"""
Contract test ensuring that the validation script aborts with the correct
DATA_BLOCKER message when required columns are missing.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def tmp_missing_columns(tmp_path):
    """Create a CSV file missing one required column."""
    csv_path = tmp_path / "incomplete.csv"
    # Include all but 'gaze_distribution'
    csv_path.write_text(
        "participant_id,fixation_duration,saccade_amplitude,recall_accuracy,valence_label,track_loss,calibrated\n"
        "P001,120.5,2.3,0.9,Positive,False,True\n"
    )
    return csv_path


def test_missing_required_columns_halts(tmp_missing_columns):
    """
    Run the validation script against a file missing a required column.
    Expect exit code 1 and the specific DATA_BLOCKER log message.
    """
    script_path = Path("code/ingestion/validate_data.py")
    # Run the script in a subprocess to capture exit code & stdout
    result = subprocess.run(
        [sys.executable, str(script_path), "--input", str(tmp_missing_columns)],
        capture_output=True,
        text=True,
    )

    # The script should exit with code 1
    assert result.returncode == 1

    # The error message must contain the exact DATA_BLOCKER token
    assert "DATA_BLOCKER: Missing required variables" in result.stderr
    # Also ensure the missing column name appears for clarity
    assert "gaze_distribution" in result.stderr

# The test can be executed via `pytest -q tests/contract/test_data_schema.py`