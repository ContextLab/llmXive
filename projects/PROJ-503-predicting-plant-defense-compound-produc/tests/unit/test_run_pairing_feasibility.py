"""
Unit tests for T014: run_pairing_feasibility.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.run_pairing_feasibility import (
    load_json_safe,
    load_geo_search_results,
    load_mw_search_results,
    extract_geo_biosample_ids,
    extract_mw_biosample_ids,
    run_pairing_feasibility
)

def test_load_json_safe_not_found():
    """Test that load_json_safe returns empty dict for missing file."""
    result = load_json_safe(Path("/nonexistent/path/file.json"))
    assert result == {}

def test_load_json_safe_valid(tmp_path):
    """Test loading a valid JSON file."""
    test_file = tmp_path / "test.json"
    data = {"key": "value"}
    with open(test_file, 'w') as f:
        json.dump(data, f)
    
    result = load_json_safe(test_file)
    assert result == data

def test_extract_geo_biosample_ids():
    """Test extraction of biosample IDs from GEO structure."""
    geo_results = {
        "Arabidopsis": [
            {
                "study_id": "GSE123",
                "samples": [
                    {"sample_id": "GSM1", "biosample_accession": "SAMN001"},
                    {"sample_id": "GSM2", "biosample_accession": "SAMN002"},
                    {"sample_id": "GSM3", "biosample_accession": "SAMN001"} # Duplicate
                ]
            }
        ],
        "Solanum": [
            {
                "study_id": "GSE456",
                "samples": [
                    {"sample_id": "GSM4", "geo_biosample": "SAMN003"}
                ]
            }
        ]
    }
    
    ids, count = extract_geo_biosample_ids(geo_results)
    assert count == 4
    assert ids == {"SAMN001", "SAMN002", "SAMN003"}

def test_extract_mw_biosample_ids():
    """Test extraction of biosample IDs from MW structure."""
    mw_results = [
        {
            "experiment_id": "MW001",
            "samples": [
                {"sample_name": "SampleA", "biosample_id": "SAMN001"},
                {"sample_name": "SampleB", "biosample_id": "SAMN004"}
            ]
        },
        {
            "experiment_id": "MW002",
            "analyses": [
                {
                    "samples": [
                        {"external_id": "SAMN005"}
                    ]
                }
            ]
        }
    ]
    
    ids, count = extract_mw_biosample_ids(mw_results)
    assert count == 3
    assert ids == {"SAMN001", "SAMN004", "SAMN005"}

def test_run_pairing_feasibility_high_rate():
    """Test pairing feasibility when rate is >= 95%."""
    geo_ids = {"SAMN001", "SAMN002", "SAMN003", "SAMN004", "SAMN005"}
    mw_ids = {"SAMN001", "SAMN002", "SAMN003", "SAMN004", "SAMN005", "SAMN006"}
    
    # Mock the extraction functions to return these sets
    with patch('code.run_pairing_feasibility.extract_geo_biosample_ids', return_value=(geo_ids, 5)), \
         patch('code.run_pairing_feasibility.extract_mw_biosample_ids', return_value=(mw_ids, 6)):
        
        report = run_pairing_feasibility({}, [])
        
        assert report["status"] == "success"
        assert report["pairing_rate"] == 1.0
        assert report["recommendation"] == "PROCEED"

def test_run_pairing_feasibility_low_rate():
    """Test pairing feasibility when rate is < 95%."""
    geo_ids = {"SAMN001", "SAMN002", "SAMN003", "SAMN004", "SAMN005"}
    mw_ids = {"SAMN001"} # Only 1 match out of 5 -> 20%
    
    with patch('code.run_pairing_feasibility.extract_geo_biosample_ids', return_value=(geo_ids, 5)), \
         patch('code.run_pairing_feasibility.extract_mw_biosample_ids', return_value=(mw_ids, 1)):
        
        report = run_pairing_feasibility({}, [])
        
        assert report["status"] == "failed"
        assert abs(report["pairing_rate"] - 0.2) < 0.01
        assert report["recommendation"] == "TRIGGER_FALLBACK_T016b"
        assert "Pairing rate" in report["message"]

def test_run_pairing_feasibility_empty_geo():
    """Test handling of empty GEO results."""
    with patch('code.run_pairing_feasibility.extract_geo_biosample_ids', return_value=(set(), 0)), \
         patch('code.run_pairing_feasibility.extract_mw_biosample_ids', return_value=({"SAMN001"}, 1)):
        
        report = run_pairing_feasibility({}, [])
        
        assert report["status"] == "failed"
        assert report["reason"] == "missing_biosample_ids"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
