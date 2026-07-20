import pytest
import os
import json
import csv
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from data.exclusion_report import map_error_reason, generate_exclusion_report, load_exclusion_logs

class TestMapErrorReason:
    def test_canonicalization_error(self):
        assert map_error_reason("SMILES canonicalization failed") == "canonicalization_error"
        assert map_error_reason("failed to canonicalize") == "canonicalization_error"

    def test_gasteiger_convergence_error(self):
        assert map_error_reason("Gasteiger convergence error") == "gasteiger_convergence_error"
        assert map_error_reason("gasteiger did not converge") == "gasteiger_convergence_error"

    def test_primary_substrate(self):
        assert map_error_reason("primary substrate filtered") == "primary_substrate_filtered"

    def test_steric_hindrance(self):
        assert map_error_reason("steric hindrance exceeded") == "steric_hindrance_exceeded"

    def test_unknown_error(self):
        assert map_error_reason("some random error") == "some random error"

class TestGenerateExclusionReport:
    def test_generates_correct_csv(self):
        logs = [
            {"row_index": 1, "reason": "SMILES canonicalization failed", "smiles": "CCO"},
            {"row_index": 2, "reason": "Gasteiger convergence error", "smiles": "CCC"},
            {"row_index": 3, "reason": "primary substrate filtered", "smiles": "CCCC"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "exclusion_report.csv"
            generate_exclusion_report(logs, output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            assert len(rows) == 3
            assert rows[0]['row_index'] == '1'
            assert rows[0]['reason'] == 'canonicalization_error'
            assert rows[0]['original_smiles'] == 'CCO'
            
            assert rows[1]['reason'] == 'gasteiger_convergence_error'
            assert rows[2]['reason'] == 'primary_substrate_filtered'

    def test_handles_missing_fields(self):
        logs = [
            {"row_index": 1, "reason": "unknown"},
            {"reason": "error", "smiles": "CC"} # Missing row_index
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "exclusion_report.csv"
            generate_exclusion_report(logs, output_path)
            
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should only have the one with row_index
            assert len(rows) == 1

class TestLoadExclusionLogs:
    def test_loads_json_array(self):
        logs_data = [
            {"row_index": 1, "reason": "test", "smiles": "CC"},
            {"row_index": 2, "reason": "test2", "smiles": "CCO"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "exclusions_test.json"
            with open(log_file, 'w') as f:
                json.dump(logs_data, f)
            
            loaded = load_exclusion_logs(Path(tmpdir))
            assert len(loaded) == 2
            assert loaded[0]['row_index'] == 1

    def test_loads_jsonl(self):
        logs_data = [
            {"row_index": 1, "reason": "test", "smiles": "CC"},
            {"row_index": 2, "reason": "test2", "smiles": "CCO"}
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "exclusions_test.json"
            with open(log_file, 'w') as f:
                for entry in logs_data:
                    f.write(json.dumps(entry) + "\n")
            
            loaded = load_exclusion_logs(Path(tmpdir))
            assert len(loaded) == 2
            
    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            loaded = load_exclusion_logs(Path(tmpdir))
            assert loaded == []