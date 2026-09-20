import pytest
import os
import csv
import json
import tempfile
import shutil
from pathlib import Path
from src.data_loader import load_public_dataset, calculate_gain_scores, log_skipped_record
from src.models import DatasetRecord


class TestDataLoader:
    """Tests for data loading functions."""
    
    def setup_method(self):
        """Setup temporary directories for tests."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = os.path.join(self.test_dir, "data")
        os.makedirs(self.data_dir)
        
    def teardown_method(self):
        """Clean up temporary directories."""
        shutil.rmtree(self.test_dir)
        
    def test_load_csv(self):
        """Test loading a CSV file."""
        csv_path = os.path.join(self.data_dir, "test.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["pre_test_score", "post_test_score", "instruction_type"])
            writer.writerow([50.0, 60.0, "embodied"])
            writer.writerow([50.0, 55.0, "static"])
            
        records = load_public_dataset(csv_path)
        assert len(records) == 2
        assert records[0].instruction_type == "embodied"
        
    def test_load_json(self):
        """Test loading a JSON file."""
        json_path = os.path.join(self.data_dir, "test.json")
        data = [
            {"pre_test_score": 50.0, "post_test_score": 60.0, "instruction_type": "embodied"},
            {"pre_test_score": 50.0, "post_test_score": 55.0, "instruction_type": "static"}
        ]
        with open(json_path, 'w') as f:
            json.dump(data, f)
            
        records = load_public_dataset(json_path)
        assert len(records) == 2
        
    def test_missing_columns_fallback(self):
        """Test fallback to synthetic when columns are missing."""
        csv_path = os.path.join(self.data_dir, "missing.csv")
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["pre_test_score", "post_test_score"])
            writer.writerow([50.0, 60.0])
            
        # Should trigger synthetic fallback
        records = load_public_dataset(csv_path)
        assert len(records) > 0
        
    def test_log_skipped_record(self):
        """Test logging skipped records."""
        log_skipped_record("Test reason", "test_source")
        # Check if log file exists (it writes to data/derivation_logs)
        log_path = Path("data/derivation_logs/skipped_records.log")
        assert log_path.exists()
