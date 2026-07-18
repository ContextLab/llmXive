"""
Unit tests for data_loader module.
"""
import pytest
import os
import csv
import json
import tempfile
import shutil
from pathlib import Path
from src.data_loader import calculate_gain_scores, log_skipped_record, load_public_dataset
from src.models import DatasetRecord


class TestDataLoader:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)

    def test_calculate_gain_scores_success(self):
        """Test that gain scores are calculated correctly for valid records."""
        records = [
            DatasetRecord(
                pre_test_score=50.0,
                post_test_score=80.0,
                instruction_type="embodied",
                covariates={}
            ),
            DatasetRecord(
                pre_test_score=60.0,
                post_test_score=60.0,
                instruction_type="static",
                covariates={}
            )
        ]

        result = calculate_gain_scores(records)

        assert len(result) == 2
        assert result[0].covariates['gain_score'] == 30.0
        assert result[1].covariates['gain_score'] == 0.0

    def test_calculate_gain_scores_missing_values(self, temp_dir):
        """Test that records with missing scores are skipped and logged."""
        # Change to temp dir to ensure log file is created there
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            records = [
                DatasetRecord(
                    pre_test_score=50.0,
                    post_test_score=80.0,
                    instruction_type="embodied",
                    covariates={}
                ),
                DatasetRecord(
                    pre_test_score=None,
                    post_test_score=80.0,
                    instruction_type="embodied",
                    covariates={}
                ),
                DatasetRecord(
                    pre_test_score=50.0,
                    post_test_score=None,
                    instruction_type="static",
                    covariates={}
                )
            ]

            result = calculate_gain_scores(records)

            # Only the first record should be processed
            assert len(result) == 1
            assert result[0].covariates['gain_score'] == 30.0

            # Check that log file was created and contains entries
            log_path = Path("data/derivation_logs/skipped_records.log")
            assert log_path.exists()

            with open(log_path, 'r') as f:
                content = f.read()
                assert "Missing pre/post scores" in content
                assert "None" in content  # Should contain the None value in JSON
        finally:
            os.chdir(original_cwd)

    def test_log_skipped_record(self, temp_dir):
        """Test that log_skipped_record creates the correct log file."""
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        try:
            record_data = {"id": 1, "value": 10}
            log_skipped_record(record_data, "Test reason")

            log_path = Path("data/derivation_logs/skipped_records.log")
            assert log_path.exists()

            with open(log_path, 'r') as f:
                content = f.read()
                assert "Reason: Test reason" in content
                assert '"id": 1' in content
        finally:
            os.chdir(original_cwd)

    def test_load_public_dataset_csv(self, temp_dir):
        """Test loading a valid CSV dataset."""
        csv_path = Path(temp_dir) / "test_data.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['pre_test_score', 'post_test_score', 'instruction_type'])
            writer.writerow(['50', '80', 'embodied'])
            writer.writerow(['60', '90', 'static'])

        records = load_public_dataset(str(csv_path))

        assert len(records) == 2
        assert records[0].pre_test_score == 50.0
        assert records[0].post_test_score == 80.0
        assert records[0].instruction_type == 'embodied'

    def test_load_public_dataset_missing_instruction_type(self, temp_dir):
        """Test that missing instruction_type triggers synthetic generation."""
        csv_path = Path(temp_dir) / "test_data_no_type.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['pre_test_score', 'post_test_score'])
            writer.writerow(['50', '80'])

        # This should trigger synthetic generation
        records = load_public_dataset(str(csv_path))

        # Should return synthetic data (default 100 samples)
        assert len(records) == 100
        assert all(r.instruction_type is not None for r in records)