import pytest
import os
import csv
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import (
    log_skipped_record,
    calculate_gain_scores,
    write_processed_data,
    load_public_dataset,
    generate_synthetic_fallback
)
from src.models import DatasetRecord

class TestDataLoader:
    """Tests for data loader functionality including gain score calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.test_dir) / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir = Path(self.test_dir) / "data" / "derivation_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test records
        self.records = [
            DatasetRecord(
                id="1",
                pre_test_score=50.0,
                post_test_score=70.0,
                instruction_type="embodied",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="2",
                pre_test_score=60.0,
                post_test_score=85.0,
                instruction_type="static",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="3",
                pre_test_score=None,  # Missing pre score
                post_test_score=75.0,
                instruction_type="embodied",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="4",
                pre_test_score=55.0,
                post_test_score=None,  # Missing post score
                instruction_type="static",
                covariates={"source": "test"}
            )
        ]

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_calculate_gain_scores_valid_records(self):
        """Test gain score calculation for valid records."""
        valid_records = [
            DatasetRecord(
                id="1",
                pre_test_score=50.0,
                post_test_score=70.0,
                instruction_type="embodied",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="2",
                pre_test_score=60.0,
                post_test_score=85.0,
                instruction_type="static",
                covariates={"source": "test"}
            )
        ]
        
        processed = calculate_gain_scores(valid_records)
        
        assert len(processed) == 2
        assert processed[0].covariates["gain_score"] == 20.0
        assert processed[1].covariates["gain_score"] == 25.0

    def test_calculate_gain_scores_excludes_missing_values(self):
        """Test that records with missing values are excluded and logged."""
        records_with_missing = [
            DatasetRecord(
                id="1",
                pre_test_score=50.0,
                post_test_score=70.0,
                instruction_type="embodied",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="2",
                pre_test_score=None,
                post_test_score=75.0,
                instruction_type="embodied",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="3",
                pre_test_score=55.0,
                post_test_score=None,
                instruction_type="static",
                covariates={"source": "test"}
            )
        ]
        
        processed = calculate_gain_scores(records_with_missing)
        
        # Only 1 record should be processed (the one with both scores)
        assert len(processed) == 1
        assert processed[0].id == "1"

    def test_log_skipped_record_creates_file(self):
        """Test that log_skipped_record creates the log file."""
        log_skipped_record(
            reason="Test missing values",
            record_id="test_123",
            dataset_source="test_dataset"
        )
        
        log_file = Path("data/derivation_logs/skipped_records.log")
        assert log_file.exists()
        
        # Clean up
        log_file.unlink()

    def test_load_public_dataset_csv(self):
        """Test loading a CSV dataset."""
        csv_path = Path(self.test_dir) / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['pre_test_score', 'post_test_score', 'instruction_type'])
            writer.writeheader()
            writer.writerow({'pre_test_score': '50', 'post_test_score': '70', 'instruction_type': 'embodied'})
            writer.writerow({'pre_test_score': '60', 'post_test_score': '85', 'instruction_type': 'static'})
        
        records = load_public_dataset(str(csv_path))
        
        assert len(records) == 2
        assert records[0].pre_test_score == 50.0
        assert records[0].post_test_score == 70.0
        assert records[0].instruction_type == "embodied"

    def test_load_public_dataset_json(self):
        """Test loading a JSON dataset."""
        json_path = Path(self.test_dir) / "test.json"
        data = [
            {"pre_test_score": 50, "post_test_score": 70, "instruction_type": "embodied"},
            {"pre_test_score": 60, "post_test_score": 85, "instruction_type": "static"}
        ]
        with open(json_path, 'w') as f:
            json.dump(data, f)
        
        records = load_public_dataset(str(json_path))
        
        assert len(records) == 2
        assert records[0].pre_test_score == 50
        assert records[0].post_test_score == 70

    def test_load_public_dataset_missing_columns(self):
        """Test handling of missing required columns."""
        csv_path = Path(self.test_dir) / "incomplete.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['pre_test_score', 'instruction_type'])
            writer.writeheader()
            writer.writerow({'pre_test_score': '50', 'instruction_type': 'embodied'})
        
        # Should log and skip the record
        records = load_public_dataset(str(csv_path))
        assert len(records) == 0

    def test_write_processed_data(self):
        """Test writing processed data to CSV."""
        records = [
            DatasetRecord(
                id="1",
                pre_test_score=50.0,
                post_test_score=70.0,
                instruction_type="embodied",
                covariates={"source": "test", "gain_score": 20.0}
            )
        ]
        
        output_path = Path(self.test_dir) / "output.csv"
        write_processed_data(records, str(output_path))
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        assert rows[0]['pre_test_score'] == '50.0'
        assert rows[0]['post_test_score'] == '70.0'
        assert rows[0]['gain_score'] == '20.0'

    def test_generate_synthetic_fallback(self):
        """Test synthetic data generation fallback."""
        records = generate_synthetic_fallback(n_samples=10, seed=42)
        
        assert len(records) == 10
        for record in records:
            assert record.pre_test_score is not None
            assert record.post_test_score is not None
            assert record.instruction_type is not None

    def test_gain_score_calculation_logic(self):
        """Test the specific logic of gain score calculation (post - pre)."""
        records = [
            DatasetRecord(
                id="1",
                pre_test_score=100.0,
                post_test_score=100.0,  # No gain
                instruction_type="embodied",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="2",
                pre_test_score=100.0,
                post_test_score=150.0,  # Positive gain
                instruction_type="static",
                covariates={"source": "test"}
            ),
            DatasetRecord(
                id="3",
                pre_test_score=100.0,
                post_test_score=80.0,   # Negative gain
                instruction_type="embodied",
                covariates={"source": "test"}
            )
        ]
        
        processed = calculate_gain_scores(records)
        
        assert processed[0].covariates["gain_score"] == 0.0
        assert processed[1].covariates["gain_score"] == 50.0
        assert processed[2].covariates["gain_score"] == -20.0