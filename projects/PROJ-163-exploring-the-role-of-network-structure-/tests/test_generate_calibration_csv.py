"""
Tests for T017: generate_calibration_csv.py
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# We need to import the script's logic. Since it's a script, we might need to
# refactor slightly for testing or import the functions if they are defined.
# For this task, we assume the script is run as an entry point, but we can test
# the helper logic if we extract it or mock the file system.
# To keep it simple and compliant with "extend existing API", we will test the
# file creation and content validation.

# Add code directory to path for imports if needed, though we mostly test file I/O
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.generate_calibration_csv import load_raw_snapshots, process_snapshot, main

class TestGenerateCalibrationCSV:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test data."""
        temp_path = tempfile.mkdtemp()
        raw_dir = Path(temp_path) / "data" / "raw"
        processed_dir = Path(temp_path) / "data" / "processed"
        raw_dir.mkdir(parents=True)
        processed_dir.mkdir(parents=True)
        yield {
            "base": Path(temp_path),
            "raw": raw_dir,
            "processed": processed_dir
        }
        shutil.rmtree(temp_path)

    @pytest.fixture
    def mock_snapshot_data(self):
        """Generate a mock backend snapshot."""
        return {
            "backend_name": "test_backend",
            "timestamp": "2023-10-27T10:00:00",
            "properties": {
                "n_qubits": 5,
                "last_update_date": "2023-10-27T10:00:00",
                "qubits": [
                    [{"name": "T1", "value": 100.0, "unit": "us"}, {"name": "T2", "value": 200.0, "unit": "us"}],
                    [{"name": "T1", "value": 150.0, "unit": "us"}, {"name": "T2", "value": 250.0, "unit": "us"}],
                    [{"name": "T1", "value": 120.0, "unit": "us"}, {"name": "T2", "value": 220.0, "unit": "us"}],
                    [{"name": "T1", "value": 130.0, "unit": "us"}, {"name": "T2", "value": 230.0, "unit": "us"}],
                    [{"name": "T1", "value": 140.0, "unit": "us"}, {"name": "T2", "value": 240.0, "unit": "us"}]
                ],
                "gates": [
                    {"gate": "cx", "qubits": [0, 1], "parameters": [{"name": "gate_error", "value": 0.01}]},
                    {"gate": "cx", "qubits": [1, 2], "parameters": [{"name": "gate_error", "value": 0.02}]}
                ],
                "readouts": [
                    {"name": "readout_error", "value": 0.05},
                    {"name": "readout_error", "value": 0.06},
                    {"name": "readout_error", "value": 0.07},
                    {"name": "readout_error", "value": 0.08},
                    {"name": "readout_error", "value": 0.09}
                ],
                "coupling_map": [[0, 1], [1, 2], [2, 3], [3, 4]]
            }
        }

    def test_load_raw_snapshots(self, temp_dir, mock_snapshot_data):
        """Test loading snapshots from a directory."""
        # Write mock data
        file_path = temp_dir["raw"] / "test_backend_20231027.json"
        with open(file_path, 'w') as f:
            json.dump(mock_snapshot_data, f)

        snapshots = load_raw_snapshots(temp_dir["raw"])
        assert len(snapshots) == 1
        assert snapshots[0]["backend_name"] == "test_backend"

    def test_process_snapshot(self, mock_snapshot_data):
        """Test processing a single snapshot."""
        # Add source file key for completeness
        mock_snapshot_data["source_file"] = "test.json"
        
        # Mock the fetcher functions to avoid dependency on real IBM logic if needed,
        # but since we are testing the logic, we rely on the existing implementation.
        # However, the existing implementation in fetcher.py might be complex.
        # We assume the extraction logic works as per T015a/T015b.
        
        # To be safe and isolated, we patch the external calls if they are heavy,
        # but here we test the structure.
        result = process_snapshot(mock_snapshot_data)
        
        assert result is not None
        assert result['device_id'] == 'test_backend'
        assert result['num_qubits'] == 5
        assert 'coupling_map_str' in result
        assert result['avg_t1'] is not None # Should be calculated average

    def test_main_creates_csv(self, temp_dir, mock_snapshot_data):
        """Test that main() creates the CSV file with correct headers."""
        # Write mock data
        file_path = temp_dir["raw"] / "test_backend_20231027.json"
        with open(file_path, 'w') as f:
            json.dump(mock_snapshot_data, f)

        # Patch the directory paths in the module
        import code.generate_calibration_csv as module
        original_raw = module.DATA_RAW_DIR
        original_processed = module.DATA_PROCESSED_DIR
        original_output = module.OUTPUT_FILE

        module.DATA_RAW_DIR = temp_dir["raw"]
        module.DATA_PROCESSED_DIR = temp_dir["processed"]
        module.OUTPUT_FILE = temp_dir["processed"] / "raw_calibration.csv"

        try:
            main()
            assert module.OUTPUT_FILE.exists()
            
            with open(module.OUTPUT_FILE, 'r') as f:
                import csv
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) > 0
                assert 'device_id' in rows[0]
                assert 'avg_t1' in rows[0]
        finally:
            # Restore
            module.DATA_RAW_DIR = original_raw
            module.DATA_PROCESSED_DIR = original_processed
            module.OUTPUT_FILE = original_output