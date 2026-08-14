"""
Integration test for missing variable error handling.
Verifies that the pipeline halts correctly when required variables are missing.
"""
import os
import json
import pytest
import subprocess
from pathlib import Path

def test_missing_variable_halt():
    """
    Run ingestion against a mock dataset missing 'SWS duration'.
    Verify system halts with specific error.
    """
    # Setup: Create a temporary mock CSV missing the required outcome
    mock_data_path = Path("data/raw/test_missing.csv")
    mock_data_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write a header that is missing 'SWS_duration' (assuming standard schema)
    with open(mock_data_path, 'w') as f:
        f.write("sample_id,taxon_A,taxon_B,REM_duration\n")
        f.write("1,0.1,0.2,1.5\n")
    
    # Run the ingestion script
    result = subprocess.run(
        ["python", "code/ingest.py", "--input", str(mock_data_path), "--mode", "validation"],
        capture_output=True,
        text=True
    )
    
    # Assert failure
    assert result.returncode != 0, "Pipeline should halt on missing variables"
    assert "missing" in result.stderr.lower() or "missing" in result.stdout.lower(), \
        "Error message should indicate missing variables"
    
    # Cleanup
    if mock_data_path.exists():
        mock_data_path.unlink()
