import pandas as pd
import pytest
import sys
from pathlib import Path
from unittest.mock import patch
from code.verify_tg import main

def test_verify_tg_success(tmp_path):
    """Test that a valid dataset passes integrity checks and writes to the log."""
    csv_path = tmp_path / "tg_dataset.csv"
    # Create a valid dataset with 500 rows and all required columns
    df = pd.DataFrame({
        'polymer_id': range(500),
        'smiles': ['C'] * 500,
        'experimental_tg': [100.0] * 500,
        'polymer_class': ['amorphous_homopolymer'] * 500
    })
    df.to_csv(csv_path, index=False)

    log_path = tmp_path / "ingest.log"

    # Mock toolkit paths to use temporary directory
    with patch('llmxive_toolkit.paths.data', return_value=csv_path), \
         patch('llmxive_toolkit.paths.path', return_value=log_path):
        main()

    assert log_path.exists(), "Log file should be created"
    assert "T_g dataset integrity check passed" in log_path.read_text()

def test_verify_tg_missing_cols(tmp_path):
    """Test that missing columns cause the script to abort (exit 1)."""
    csv_path = tmp_path / "tg_dataset.csv"
    # Missing 'experimental_tg'
    df = pd.DataFrame({
        'polymer_id': range(500),
        'smiles': ['C'] * 500,
        'polymer_class': ['amorphous_homopolymer'] * 500
    })
    df.to_csv(csv_path, index=False)

    with patch('llmxive_toolkit.paths.data', return_value=csv_path), \
         patch('llmxive_toolkit.paths.path', return_value=tmp_path / "log"):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

def test_verify_tg_too_short(tmp_path):
    """Test that insufficient row count causes the script to abort (exit 1)."""
    csv_path = tmp_path / "tg_dataset.csv"
    # Only 100 rows instead of 500
    df = pd.DataFrame({
        'polymer_id': range(100),
        'smiles': ['C'] * 100,
        'experimental_tg': [100.0] * 100,
        'polymer_class': ['amorphous_homopolymer'] * 100
    })
    df.to_csv(csv_path, index=False)

    with patch('llmxive_toolkit.paths.data', return_value=csv_path), \
         patch('llmxive_toolkit.paths.path', return_value=tmp_path / "log"):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1

def test_verify_tg_file_not_found():
    """Test that a missing file causes the script to abort (exit 1)."""
    with patch('llmxive_toolkit.paths.data', return_value=Path("non_existent.csv")), \
         patch('llmxive_toolkit.paths.path', return_value=Path("log")):
        with pytest.raises(SystemExit) as e:
            main()
        assert e.value.code == 1