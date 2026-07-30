import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.data.download import (
    get_file_hash,
    validate_record_metadata,
    fetch_tuh_metadata,
    process_and_validate
)

def test_get_file_hash():
    """Test SHA-256 hash calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test data")
        temp_path = f.name
    
    try:
        hash_value = get_file_hash(Path(temp_path))
        assert len(hash_value) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in hash_value)
    finally:
        os.unlink(temp_path)

def test_validate_record_metadata_valid():
    """Test validation of a valid record."""
    registry = ["MMSE", "MoCA"]
    record = {
        "age": 25,
        "cognitive_instrument": "MMSE"
    }
    
    result = validate_record_metadata(record, registry)
    assert result["status"] == "Valid"
    assert len(result["issues"]) == 0

def test_validate_record_metadata_missing_age():
    """Test validation of a record with missing age."""
    registry = ["MMSE", "MoCA"]
    record = {
        "age": None,
        "cognitive_instrument": "MMSE"
    }
    
    result = validate_record_metadata(record, registry)
    assert result["status"] == "Invalid"
    assert "Missing age" in result["issues"]

def test_validate_record_metadata_young_age():
    """Test validation of a record with age < 18."""
    registry = ["MMSE", "MoCA"]
    record = {
        "age": 16,
        "cognitive_instrument": "MMSE"
    }
    
    result = validate_record_metadata(record, registry)
    assert result["status"] == "Invalid"
    assert "Age 16 < 18" in result["issues"]

def test_validate_record_metadata_missing_cognitive():
    """Test validation of a record with missing cognitive data."""
    registry = ["MMSE", "MoCA"]
    record = {
        "age": 25,
        "cognitive_instrument": None
    }
    
    result = validate_record_metadata(record, registry)
    assert result["status"] == "Missing Cognitive Data"
    assert "Missing Cognitive Data" in result["issues"]

def test_validate_record_metadata_invalid_instrument():
    """Test validation of a record with invalid cognitive instrument."""
    registry = ["MMSE", "MoCA"]
    record = {
        "age": 25,
        "cognitive_instrument": "InvalidInstrument"
    }
    
    result = validate_record_metadata(record, registry)
    assert result["status"] == "Invalid Instrument"
    assert "Invalid Instrument: InvalidInstrument" in result["issues"]

def test_process_and_validate():
    """Test the full processing and validation pipeline."""
    registry = ["MMSE", "MoCA"]
    metadata = [
        {
            "participant_id": "sub_001",
            "age": 25,
            "cognitive_instrument": "MMSE"
        },
        {
            "participant_id": "sub_002",
            "age": 16,
            "cognitive_instrument": "MMSE"
        },
        {
            "participant_id": "sub_003",
            "age": 30,
            "cognitive_instrument": None
        },
        {
            "participant_id": "sub_004",
            "age": 40,
            "cognitive_instrument": "InvalidInstrument"
        }
    ]
    
    result = process_and_validate(metadata, registry)
    
    assert result["valid_count"] == 1
    assert result["invalid_instrument_count"] == 1
    assert result["missing_cognitive_count"] == 1
    assert result["total_count"] == 4
    assert result["status"] == "OK"
    
    # Check record statuses
    statuses = {r["participant_id"]: r["status"] for r in result["records"]}
    assert statuses["sub_001"] == "Valid"
    assert statuses["sub_002"] == "Invalid"
    assert statuses["sub_003"] == "Missing Cognitive Data"
    assert statuses["sub_004"] == "Invalid Instrument"

def test_process_and_validate_blocked_status():
    """Test that BLOCKED status is set when all records are missing cognitive data."""
    registry = ["MMSE", "MoCA"]
    metadata = [
        {
            "participant_id": "sub_001",
            "age": 25,
            "cognitive_instrument": None
        },
        {
            "participant_id": "sub_002",
            "age": 30,
            "cognitive_instrument": None
        }
    ]
    
    result = process_and_validate(metadata, registry)
    
    assert result["valid_count"] == 0
    assert result["invalid_instrument_count"] == 0
    assert result["missing_cognitive_count"] == 2
    assert result["total_count"] == 2
    assert result["status"] == "BLOCKED"
    assert result["reason"] == "No linked cognitive data found in TUH Corpus"

@patch('code.data.download.load_dataset')
def test_fetch_tuh_metadata(mock_load_dataset):
    """Test fetching TUH metadata with mocked dataset."""
    # Mock the dataset iterator
    mock_record1 = {"subject": "sub_001", "age": 25, "cognitive_score": "MMSE", "file": "file1.edf"}
    mock_record2 = {"subject": "sub_002", "age": 30, "cognitive_score": "MoCA", "file": "file2.edf"}
    
    mock_dataset = MagicMock()
    mock_dataset.__iter__ = MagicMock(return_value=iter([mock_record1, mock_record2]))
    mock_load_dataset.return_value = mock_dataset
    
    records = fetch_tuh_metadata()
    
    assert len(records) == 2
    assert records[0]["participant_id"] == "sub_001"
    assert records[0]["age"] == 25
    assert records[0]["cognitive_instrument"] == "MMSE"
    assert records[1]["participant_id"] == "sub_002"
    assert records[1]["age"] == 30
    assert records[1]["cognitive_instrument"] == "MoCA"
    
    mock_load_dataset.assert_called_once_with("physionet/tuh_eeg", split="train", streaming=True)
