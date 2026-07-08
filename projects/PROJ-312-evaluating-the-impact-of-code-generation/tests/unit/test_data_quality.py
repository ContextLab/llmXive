"""
Unit tests for data quality validation module (T018b).
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from data_quality import calculate_success_rate, validate_and_check_quality, DataQualityError

class TestCalculateSuccessRate:
    def test_normal_case(self):
        """Test normal calculation."""
        result = calculate_success_rate(95, 100)
        assert result == 0.95

    def test_perfect_score(self):
        """Test perfect score."""
        result = calculate_success_rate(100, 100)
        assert result == 1.0

    def test_zero_total(self):
        """Test with zero total."""
        result = calculate_success_rate(0, 0)
        assert result == 0.0

    def test_partial_success(self):
        """Test partial success."""
        result = calculate_success_rate(50, 100)
        assert result == 0.5

class TestValidateAndCheckQuality:
    def setup_method(self):
        """Setup temporary files for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.processed_file = os.path.join(self.temp_dir, "processed_prs.json")
        self.stats_file = os.path.join(self.temp_dir, "processing_stats.json")

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_success_rate_above_threshold(self):
        """Test that success rate above threshold passes."""
        # Create valid processed data
        valid_data = [{"pr_id": "1", "repo_name": "test", "turnaround_hours": 10} for _ in range(95)]
        with open(self.processed_file, 'w') as f:
            json.dump(valid_data, f)

        with open(self.stats_file, 'w') as f:
            json.dump({"total_prs_processed": 100}, f)

        result = validate_and_check_quality(
            processed_data_path=self.processed_file,
            total_prs_attempted=100,
            quality_threshold=0.95
        )

        assert result["status"] == "passed"
        assert result["success_rate"] == 0.95

    def test_success_rate_below_threshold(self):
        """Test that success rate below threshold raises DataQualityError."""
        # Create processed data with low success rate
        valid_data = [{"pr_id": "1", "repo_name": "test", "turnaround_hours": 10} for _ in range(50)]
        with open(self.processed_file, 'w') as f:
            json.dump(valid_data, f)

        with open(self.stats_file, 'w') as f:
            json.dump({"total_prs_processed": 100}, f)

        with pytest.raises(DataQualityError) as exc_info:
            validate_and_check_quality(
                processed_data_path=self.processed_file,
                total_prs_attempted=100,
                quality_threshold=0.95
            )

        assert "Data quality threshold not met" in str(exc_info.value)

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            validate_and_check_quality(
                processed_data_path="/nonexistent/file.json",
                total_prs_attempted=100
            )

    def test_empty_processed_data(self):
        """Test with empty processed data."""
        with open(self.processed_file, 'w') as f:
            json.dump([], f)

        with open(self.stats_file, 'w') as f:
            json.dump({"total_prs_processed": 100}, f)

        with pytest.raises(DataQualityError) as exc_info:
            validate_and_check_quality(
                processed_data_path=self.processed_file,
                total_prs_attempted=100,
                quality_threshold=0.95
            )

        assert "Data quality threshold not met" in str(exc_info.value)