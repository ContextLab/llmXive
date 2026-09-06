"""
Unit tests for validate_and_load_golden_set.py (Task T007f).
"""
import pytest
import pandas as pd
from pathlib import Path
import os
import sys
import tempfile
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from validate_and_load_golden_set import validate_golden_set_csv, check_public_self_reports

class TestValidateGoldenSetCSV:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = Path(self.temp_dir) / "golden_set.csv"

    def teardown_method(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_valid_golden_set(self):
        # Create a valid golden set
        data = {
            'interaction_id': [f'id_{i}' for i in range(50)],
            'expert_load_score': [50.0] * 50
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_file, index=False)

        assert validate_golden_set_csv(self.test_file) is True

    def test_missing_file(self):
        assert validate_golden_set_csv(Path("non_existent_file.csv")) is False

    def test_missing_columns(self):
        data = {
            'interaction_id': [f'id_{i}' for i in range(50)],
            'wrong_column': [50.0] * 50
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_file, index=False)

        assert validate_golden_set_csv(self.test_file) is False

    def test_insufficient_rows(self):
        data = {
            'interaction_id': [f'id_{i}' for i in range(49)],
            'expert_load_score': [50.0] * 49
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_file, index=False)

        assert validate_golden_set_csv(self.test_file) is False

    def test_invalid_score_range(self):
        data = {
            'interaction_id': [f'id_{i}' for i in range(50)],
            'expert_load_score': [150.0] * 50
        }
        df = pd.DataFrame(data)
        df.to_csv(self.test_file, index=False)

        assert validate_golden_set_csv(self.test_file) is False

class TestCheckPublicSelfReports:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        Path("data/processed").mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_marker_exists(self):
        marker = Path("data/processed/.has_self_reports")
        marker.touch()
        assert check_public_self_reports() is True

    def test_no_marker_and_no_data(self):
        assert check_public_self_reports() is False

    def test_data_with_self_report_column(self):
        # Create a mock dataset file
        data_path = Path("data/processed/assistments_dataset.csv")
        data = {
            'interaction_id': ['id_1'],
            'nasa_tlx': [80]
        }
        pd.DataFrame(data).to_csv(data_path, index=False)
        
        assert check_public_self_reports() is True