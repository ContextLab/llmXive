"""
Unit tests for the uncertainty flagger module (Task T013c).
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
import os
# Ensure code directory is in path for imports
code_path = Path(__file__).resolve().parent.parent.parent / "code"
sys.path.insert(0, str(code_path))

from uncertainty_flagger import (
    flag_default_uncertainty_entries,
    DEFAULT_UNCERTAINTY_COVERAGE
)

# Mock metadata for testing
MOCK_METADATA_ENTRIES = [
    {
        "entry_id": "entry_001",
        "uncertainty_raw": "±5°C",
        "instrument": "TGA-500"
    },
    {
        "entry_id": "entry_002",
        "uncertainty_raw": "±10°C",
        "instrument": "TGA-500"
    },
    {
        "entry_id": "entry_003",
        "uncertainty_raw": "Unknown",
        "instrument": "TGA-500"
    },
    {
        "entry_id": "entry_004",
        "uncertainty_raw": "",
        "instrument": "TGA-500"
    }
]

def test_flag_default_uncertainty_entries():
    """Test that entries are correctly flagged based on uncertainty values."""
    result = flag_default_uncertainty_entries(MOCK_METADATA_ENTRIES)
    
    assert "flags" in result
    assert "summary" in result
    assert len(result["flags"]) == 4
    
    # Check specific flags
    flags_by_id = {f["entry_id"]: f for f in result["flags"]}
    
    # entry_001: ±5°C -> Explicit, non-default
    assert flags_by_id["entry_001"]["is_default_bound"] is False
    assert flags_by_id["entry_001"]["uncertainty_source"] == "explicit"
    assert flags_by_id["entry_001"]["uncertainty_value"] == 5.0
    
    # entry_002: ±10°C -> Explicit, but matches default
    assert flags_by_id["entry_002"]["is_default_bound"] is True
    assert flags_by_id["entry_002"]["uncertainty_source"] == "explicit_default"
    assert flags_by_id["entry_002"]["uncertainty_value"] == 10.0
    
    # entry_003: Unknown -> Default applied
    assert flags_by_id["entry_003"]["is_default_bound"] is True
    assert flags_by_id["entry_003"]["uncertainty_source"] == "default_applied"
    assert flags_by_id["entry_003"]["uncertainty_value"] == DEFAULT_UNCERTAINTY_COVERAGE
    
    # entry_004: Empty -> Default applied
    assert flags_by_id["entry_004"]["is_default_bound"] is True
    assert flags_by_id["entry_004"]["uncertainty_source"] == "default_applied"
    assert flags_by_id["entry_004"]["uncertainty_value"] == DEFAULT_UNCERTAINTY_COVERAGE

def test_summary_statistics():
    """Test that summary statistics are calculated correctly."""
    result = flag_default_uncertainty_entries(MOCK_METADATA_ENTRIES)
    
    summary = result["summary"]
    assert summary["total_entries"] == 4
    assert summary["default_bound_count"] == 3  # 002, 003, 004
    assert summary["explicit_non_default_count"] == 1  # 001
    assert summary["default_threshold"] == DEFAULT_UNCERTAINTY_COVERAGE

def test_empty_metadata():
    """Test handling of empty metadata list."""
    result = flag_default_uncertainty_entries([])
    
    assert result["flags"] == []
    assert result["summary"]["total_entries"] == 0
    assert result["summary"]["default_bound_count"] == 0
    assert result["summary"]["explicit_non_default_count"] == 0