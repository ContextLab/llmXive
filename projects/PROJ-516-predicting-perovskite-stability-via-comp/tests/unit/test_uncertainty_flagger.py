"""
Unit tests for the uncertainty flagging module.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from uncertainty_flagger import (
    load_metadata,
    flag_default_uncertainty_entries,
    save_flags,
    DEFAULT_UNCERTAINTY_CELSIUS,
    DEFAULT_FLAG_VALUE,
    EXPLICIT_FLAG_VALUE
)
from data_ingestion_metadata import parse_uncertainty

@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return [
        {
            "id": "entry_1",
            "formula": "CsPbI3",
            "uncertainty": "±5°C",
            "instrument": "TGA Q500"
        },
        {
            "id": "entry_2",
            "formula": "MAPbI3",
            "uncertainty": None,
            "instrument": "Unknown"
        },
        {
            "id": "entry_3",
            "formula": "FAPbBr3",
            "uncertainty": "",
            "instrument": "TGA 8000"
        },
        {
            "id": "entry_4",
            "formula": "CsSnI3",
            "uncertainty": "±10°C",
            "instrument": "TGA Q50"
        }
    ]

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    return tmp_path

def test_parse_uncertainty_valid():
    """Test parsing a valid uncertainty string."""
    result = parse_uncertainty("±5°C")
    assert result is not None
    assert result['value'] == 5.0
    assert result['unit'] == 'C'

def test_parse_uncertainty_none():
    """Test parsing None."""
    result = parse_uncertainty(None)
    assert result is None

def test_parse_uncertainty_empty():
    """Test parsing empty string."""
    result = parse_uncertainty("")
    assert result is None

def test_flag_default_uncertainty_entries(sample_metadata):
    """Test that entries are correctly flagged based on uncertainty."""
    flagged = flag_default_uncertainty_entries(sample_metadata)
    
    # Entry 1: Explicit ±5°C
    assert flagged[0]['uncertainty_flag'] == EXPLICIT_FLAG_VALUE
    assert flagged[0]['T_d_uncertainty'] == 5.0

    # Entry 2: None -> Default
    assert flagged[1]['uncertainty_flag'] == DEFAULT_FLAG_VALUE
    assert flagged[1]['T_d_uncertainty'] == DEFAULT_UNCERTAINTY_CELSIUS

    # Entry 3: Empty string -> Default
    assert flagged[2]['uncertainty_flag'] == DEFAULT_FLAG_VALUE
    assert flagged[2]['T_d_uncertainty'] == DEFAULT_UNCERTAINTY_CELSIUS

    # Entry 4: Explicit ±10°C (even if it matches default, it's explicit)
    assert flagged[3]['uncertainty_flag'] == EXPLICIT_FLAG_VALUE
    assert flagged[3]['T_d_uncertainty'] == 10.0

def test_save_flags(temp_output_dir, sample_metadata):
    """Test saving flags to a JSON file."""
    flagged = flag_default_uncertainty_entries(sample_metadata)
    output_path = temp_output_dir / "test_flags.json"
    
    save_flags(flagged, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    assert len(saved_data) == len(sample_metadata)
    assert saved_data[0]['uncertainty_flag'] == EXPLICIT_FLAG_VALUE
    assert saved_data[1]['uncertainty_flag'] == DEFAULT_FLAG_VALUE

def test_load_metadata_missing_file(tmp_path):
    """Test loading a non-existent file raises error."""
    non_existent = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        load_metadata(non_existent)