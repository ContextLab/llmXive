import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Setup paths for testing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

def test_extract_geo_biosample_ids():
    """Test extraction of biosample IDs from GEO data structures."""
    from run_pairing_feasibility import extract_geo_biosample_ids

    # Case 1: List of dicts with 'samples'
    data = [
        {"accession": "GSE123", "samples": ["GSM1", "GSM2"]},
        {"accession": "GSE456", "samples": ["GSM3"]}
    ]
    result = extract_geo_biosample_ids(data)
    assert result == {"GSM1", "GSM2", "GSM3"}

    # Case 2: List of dicts with 'gsm'
    data = [
        {"accession": "GSE123", "gsm": ["GSM1", "GSM2"]}
    ]
    result = extract_geo_biosample_ids(data)
    assert result == {"GSM1", "GSM2"}

    # Case 3: No sample info (should return empty)
    data = [{"accession": "GSE123"}]
    result = extract_geo_biosample_ids(data)
    assert len(result) == 0

def test_extract_mw_biosample_ids():
    """Test extraction of biosample IDs from MW data structures."""
    from run_pairing_feasibility import extract_mw_biosample_ids

    # Case 1: List of dicts with 'samples'
    data = [
        {"study": "S1", "samples": ["MW1", "MW2"]}
    ]
    result = extract_mw_biosample_ids(data)
    assert result == {"MW1", "MW2"}

    # Case 2: List of dicts with 'biosamples'
    data = [
        {"biosamples": ["MW3", "MW4"]}
    ]
    result = extract_mw_biosample_ids(data)
    assert result == {"MW3", "MW4"}

    # Case 3: No sample info
    data = [{"study": "S1"}]
    result = extract_mw_biosample_ids(data)
    assert len(result) == 0

def test_run_pairing_feasibility_integration(tmp_path):
    """
    Integration test for the main function with mock data files.
    """
    import run_pairing_feasibility
    from run_pairing_feasibility import run_pairing_feasibility, DATA_RAW_DIR, DATA_PAIRED_DIR, LOGS_DIR
    
    # Create temporary directories
    temp_raw = tmp_path / "data" / "raw"
    temp_raw.mkdir(parents=True)
    temp_paired = tmp_path / "data" / "paired"
    temp_paired.mkdir()
    temp_logs = tmp_path / "logs"
    temp_logs.mkdir()

    # Mock data
    geo_arab = [
        {"accession": "GSE1", "samples": ["GSM100", "GSM101"]},
        {"accession": "GSE2", "samples": ["GSM102"]}
    ]
    geo_solanum = [
        {"accession": "GSE3", "samples": ["GSM200", "GSM201"]}
    ]
    mw_data = [
        {"study": "MW1", "samples": ["GSM100", "GSM102", "GSM200"]}
    ]

    # Write mock files
    with open(temp_raw / "geo_arabidopsis_search.json", 'w') as f:
        json.dump(geo_arab, f)
    with open(temp_raw / "geo_solanum_search.json", 'w') as f:
        json.dump(geo_solanum, f)
    with open(temp_raw / "mw_search.json", 'w') as f:
        json.dump(mw_data, f)

    # Patch paths
    with patch.object(run_pairing_feasibility, 'DATA_RAW_DIR', temp_raw), \
         patch.object(run_pairing_feasibility, 'DATA_PAIRED_DIR', temp_paired), \
         patch.object(run_pairing_feasibility, 'LOGS_DIR', temp_logs):
        
        run_pairing_feasibility()

        # Verify outputs
        report_path = temp_paired / "pairing_report.json"
        assert report_path.exists()
        
        with open(report_path) as f:
            report = json.load(f)
        
        # Expected: GSM100, GSM102, GSM200 matched (3 out of 5 GEO samples)
        # GEO samples: GSM100, GSM101, GSM102, GSM200, GSM201 (Total 5)
        # MW samples: GSM100, GSM102, GSM200 (Total 3)
        # Matched: GSM100, GSM102, GSM200 (3)
        # Rate: 3/5 = 0.6
        assert report["matched_samples"] == 3
        assert report["geo_samples"] == 5
        assert report["mw_samples"] == 3
        assert abs(report["pairing_rate"] - 0.6) < 0.001
        assert report["status"] == "insufficient"

        log_path = temp_logs / "data_pairing.json"
        assert log_path.exists()