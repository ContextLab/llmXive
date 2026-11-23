import pytest
import json
import csv
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.exclusion_report import load_exclusion_logs, map_error_reason, generate_exclusion_report

def test_map_error_reason():
    """Test mapping of raw error strings to schema codes."""
    assert map_error_reason('SMILES canonicalization failed') == 'canonicalization_error'
    assert map_error_reason('Gasteiger convergence error') == 'gasteiger_convergence_error'
    assert map_error_reason('Primary substrate') == 'primary_substrate_filter'
    assert map_error_reason('ambiguous_stereochemistry') == 'ambiguous_stereochemistry'
    # Test passthrough for unknown (should return original)
    assert map_error_reason('Unknown Error') == 'Unknown Error'

def test_load_exclusion_logs_jsonl():
    """Test loading logs from JSONL format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        log_path = Path(tmpdir) / "test.log"
        
        # Write test data
        test_data = [
            {"row_index": 1, "reason": "SMILES canonicalization failed", "original_smiles": "CCO"},
            {"row_index": 2, "reason": "Primary substrate", "original_smiles": "C(C)C"},
            {"row_index": 3, "reason": "Gasteiger convergence error", "original_smiles": "CCC"}
        ]
        
        with open(log_path, 'w') as f:
            for entry in test_data:
                f.write(json.dumps(entry) + '\n')
        
        loaded = load_exclusion_logs([str(log_path)])
        
        assert len(loaded) == 3
        assert loaded[0]['row_index'] == 1
        assert loaded[0]['reason'] == "SMILES canonicalization failed"

def test_generate_exclusion_report():
    """Test generation of the CSV report."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.csv"
        
        entries = [
            {"row_index": 1, "reason": "SMILES canonicalization failed", "original_smiles": "CCO"},
            {"row_index": 2, "reason": "Primary substrate", "original_smiles": "C(C)C"}
        ]
        
        generate_exclusion_report(entries, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        assert len(rows) == 2
        assert rows[0]['row_index'] == '1'
        assert rows[0]['reason'] == 'canonicalization_error'
        assert rows[0]['original_smiles'] == 'CCO'
        assert rows[1]['reason'] == 'primary_substrate_filter'
        
def test_load_exclusion_logs_missing_file():
    """Test behavior when log file is missing."""
    loaded = load_exclusion_logs(['/nonexistent/path.log'])
    assert len(loaded) == 0