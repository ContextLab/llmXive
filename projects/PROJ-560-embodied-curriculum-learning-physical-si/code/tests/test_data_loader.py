import pytest
import os
import csv
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add src to path if not already
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import load_public_dataset, calculate_gain_scores
from src.models import DatasetRecord

class TestDataLoader:
    
    def setup_method(self):
        """Setup test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.input_csv = Path(self.test_dir) / "input.csv"
        self.input_json = Path(self.test_dir) / "input.json"
        self.output_csv = Path(self.test_dir) / "output.csv"
        self.log_path = Path(self.test_dir) / "skipped.log"

    def teardown_method(self):
        """Cleanup test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_load_csv_with_instruction_type(self):
        """Test loading CSV that already has instruction_type."""
        data = [
            {"pre_test_score": 10, "post_test_score": 15, "instruction_type": "embodied"},
            {"pre_test_score": 12, "post_test_score": 14, "instruction_type": "static"},
        ]
        
        with open(self.input_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        records = load_public_dataset(str(self.input_csv), str(self.output_csv))
        
        assert len(records) == 2
        assert records[0].instruction_type == "embodied"
        assert records[1].instruction_type == "static"
        assert Path(self.output_csv).exists()

    def test_load_csv_missing_instruction_type_triggers_synthetic(self):
        """Test that missing instruction_type triggers synthetic generation (FR-008)."""
        # Data without instruction_type
        data = [
            {"pre_test_score": 10, "post_test_score": 15},
            {"pre_test_score": 12, "post_test_score": 14},
        ]
        
        with open(self.input_csv, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

        # This should not raise an error, but generate synthetic data
        records = load_public_dataset(
            str(self.input_csv), 
            str(self.output_csv),
            seed=42,
            synthetic_params={"n_samples": 5}
        )
        
        # Should have generated synthetic records (default or specified)
        assert len(records) >= 1 # At least some records
        # Verify all records now have instruction_type
        for r in records:
            assert r.instruction_type in ["embodied", "static"]

    def test_load_json_missing_instruction_type(self):
        """Test JSON loading with missing instruction_type."""
        data = [
            {"pre_test_score": 10, "post_test_score": 15},
            {"pre_test_score": 12, "post_test_score": 14},
        ]
        
        with open(self.input_json, 'w') as f:
            json.dump(data, f)

        records = load_public_dataset(
            str(self.input_json),
            str(self.output_csv),
            seed=42,
            synthetic_params={"n_samples": 3}
        )
        
        assert len(records) == 3
        for r in records:
            assert r.instruction_type is not None

    def test_calculate_gain_scores(self):
        """Test gain score calculation and skipping logic."""
        records = [
            DatasetRecord(pre_test_score=10.0, post_test_score=15.0, instruction_type="embodied", covariates={}),
            DatasetRecord(pre_test_score=12.0, post_test_score=None, instruction_type="static", covariates={}), # Missing
            DatasetRecord(pre_test_score=10.0, post_test_score=14.0, instruction_type="embodied", covariates={}),
        ]
        
        valid_records = calculate_gain_scores(records, str(self.log_path))
        
        assert len(valid_records) == 2
        assert Path(self.log_path).exists()
        
        # Check log content
        with open(self.log_path, 'r') as f:
            content = f.read()
            assert "Skipped 1 records" in content

    def test_invalid_file_format(self):
        """Test error on unsupported file format."""
        invalid_file = Path(self.test_dir) / "data.txt"
        invalid_file.touch()
        
        with pytest.raises(ValueError):
            load_public_dataset(str(invalid_file), str(self.output_csv))