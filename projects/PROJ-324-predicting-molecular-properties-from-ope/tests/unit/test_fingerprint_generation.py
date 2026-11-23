"""
Unit tests for fingerprint generation module.
"""

import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.fingerprint import (
    check_obabel_available,
    smiles_to_obabel_fingerprint,
    parse_fingerprint_string,
    process_dataset
)

def test_parse_fingerprint_string():
    """Test parsing of fingerprint strings."""
    # Test valid string
    fp_str = "1 0 1 1 0"
    result = parse_fingerprint_string(fp_str, "ECFP4")
    assert result == "1 0 1 1 0"

    # Test NULL
    result = parse_fingerprint_string("NULL", "ECFP4")
    assert result == "NULL"

    # Test None
    result = parse_fingerprint_string(None, "ECFP4")
    assert result == "NULL"

def test_process_dataset():
    """Test processing a dataset to generate fingerprints."""
    # Create a temporary input file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("smiles\n")
        f.write("CCO\n") # Ethanol
        f.write("CC(=O)O\n") # Acetic acid
        temp_input = f.name

    # Create a temporary output file path
    temp_output = tempfile.mktemp(suffix='.csv')

    try:
        # Mock the obabel subprocess call to return fake fingerprints
        mock_output = "CCO\n1 0 1 0 1\nCC(=O)O\n0 1 0 1 0"

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=mock_output,
                stderr=""
            )

            process_dataset(temp_input, temp_output, ["ECFP4"])

            # Check output file exists
            assert os.path.exists(temp_output)

            # Read and verify content
            df = pd.read_csv(temp_output)
            assert "smiles" in df.columns
            assert "fp_ECFP4" in df.columns
            assert len(df) == 2

    finally:
        # Cleanup
        if os.path.exists(temp_input):
            os.remove(temp_input)
        if os.path.exists(temp_output):
            os.remove(temp_output)

def test_check_obabel_available():
    """Test checking obabel availability (mocked)."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        assert check_obabel_available() is True

    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        assert check_obabel_available() is False

if __name__ == "__main__":
    test_parse_fingerprint_string()
    test_process_dataset()
    test_check_obabel_available()
    print("All tests passed.")
