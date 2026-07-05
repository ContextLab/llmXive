"""
Unit tests for main.py validation logic.

Tests the ERR_INSUFFICIENT_DATA handling and dataset validation.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config import CONFIG, ERR_INSUFFICIENT_DATA
from main import validate_dataset_min_rows

@pytest.fixture
def temp_csv(tmp_path):
    """Create a temporary CSV file for testing."""
    csv_path = tmp_path / "test_merged.csv"
    return csv_path

def test_validate_dataset_insufficient_rows(temp_csv, tmp_path):
    """Test that validation fails when rows < 20."""
    # Create a CSV with only 10 rows
    df = pd.DataFrame({
        'yield_strength_MPa': range(10),
        'shear_modulus_GPa': range(10)
    })
    df.to_csv(temp_csv, index=False)
    
    # Mock the CONFIG.INTERMEDIATE_DATA_DIR to point to our temp file
    with patch('main.CONFIG') as mock_config:
        mock_config.INTERMEDIATE_DATA_DIR = str(tmp_path)
        
        # Should raise SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            validate_dataset_min_rows(min_rows=20)
        
        assert exc_info.value.code == 1

def test_validate_dataset_sufficient_rows(temp_csv, tmp_path):
    """Test that validation passes when rows >= 20."""
    # Create a CSV with 25 rows
    df = pd.DataFrame({
        'yield_strength_MPa': range(25),
        'shear_modulus_GPa': range(25)
    })
    df.to_csv(temp_csv, index=False)
    
    with patch('main.CONFIG') as mock_config:
        mock_config.INTERMEDIATE_DATA_DIR = str(tmp_path)
        
        # Should return True without raising
        result = validate_dataset_min_rows(min_rows=20)
        assert result is True

def test_validate_dataset_missing_file(tmp_path):
    """Test that validation fails when file doesn't exist."""
    with patch('main.CONFIG') as mock_config:
        mock_config.INTERMEDIATE_DATA_DIR = str(tmp_path / "nonexistent")
        
        with pytest.raises(SystemExit) as exc_info:
            validate_dataset_min_rows(min_rows=20)
        
        assert exc_info.value.code == 1

def test_validate_dataset_missing_columns(temp_csv, tmp_path):
    """Test that validation fails when required columns are missing."""
    # Create a CSV with missing columns
    df = pd.DataFrame({
        'yield_strength_MPa': range(25),
        # Missing 'shear_modulus_GPa'
    })
    df.to_csv(temp_csv, index=False)
    
    with patch('main.CONFIG') as mock_config:
        mock_config.INTERMEDIATE_DATA_DIR = str(tmp_path)
        
        with pytest.raises(SystemExit) as exc_info:
            validate_dataset_min_rows(min_rows=20)
        
        assert exc_info.value.code == 1