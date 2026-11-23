import pytest
import os
import csv
from pathlib import Path
import tempfile
import shutil

from code.data.verify_output import verify_csv_artifact, verify_log_artifact

class TestVerifyOutput:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp = tempfile.mkdtemp()
        yield Path(temp)
        shutil.rmtree(temp)

    def test_csv_exists_and_valid(self, temp_dir):
        """Test verification of a valid CSV with required columns."""
        csv_path = temp_dir / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2', 'col3'])
            writer.writeheader()
            writer.writerow({'col1': 'a', 'col2': 'b', 'col3': 'c'})
            writer.writerow({'col1': 'd', 'col2': 'e', 'col3': 'f'})

        required = ['col1', 'col2', 'col3']
        report = verify_csv_artifact(csv_path, required)

        assert report['exists'] is True
        assert report['is_empty'] is False
        assert report['row_count'] == 2
        assert report['columns_match'] is True
        assert report['valid'] is True
        assert len(report['missing_columns']) == 0

    def test_csv_missing_columns(self, temp_dir):
        """Test verification when required columns are missing."""
        csv_path = temp_dir / "test.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['col1', 'col2'])
            writer.writeheader()
            writer.writerow({'col1': 'a', 'col2': 'b'})

        required = ['col1', 'col2', 'col3']
        report = verify_csv_artifact(csv_path, required)

        assert report['exists'] is True
        assert report['columns_match'] is False
        assert report['valid'] is False
        assert 'col3' in report['missing_columns']

    def test_csv_not_exists(self, temp_dir):
        """Test verification when file does not exist."""
        csv_path = temp_dir / "nonexistent.csv"
        required = ['col1']
        report = verify_csv_artifact(csv_path, required)

        assert report['exists'] is False
        assert report['valid'] is False

    def test_log_exists_and_valid(self, temp_dir):
        """Test verification of a valid log file."""
        log_path = temp_dir / "test.log"
        log_path.write_text("Line 1\nLine 2\nLine 3\n")

        report = verify_log_artifact(log_path, min_lines=2)

        assert report['exists'] is True
        assert report['line_count'] == 3
        assert report['min_lines_met'] is True
        assert report['valid'] is True

    def test_log_below_min_lines(self, temp_dir):
        """Test verification when log has fewer lines than required."""
        log_path = temp_dir / "test.log"
        log_path.write_text("Line 1\n")

        report = verify_log_artifact(log_path, min_lines=5)

        assert report['exists'] is True
        assert report['line_count'] == 1
        assert report['min_lines_met'] is False
        assert report['valid'] is False

    def test_log_not_exists(self, temp_dir):
        """Test verification when log file does not exist."""
        log_path = temp_dir / "nonexistent.log"
        report = verify_log_artifact(log_path, min_lines=1)

        assert report['exists'] is False
        assert report['valid'] is False
