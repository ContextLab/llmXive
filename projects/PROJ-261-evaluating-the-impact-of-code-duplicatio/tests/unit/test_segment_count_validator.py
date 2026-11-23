import pytest
import csv
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from segment_count_validator import (
    validate_segment_count,
    validate_all_required_files,
    load_processed_csv
)


class TestSegmentCountValidator:
    """Tests for segment count validation functionality."""

    @pytest.fixture
    def temp_csv_file(self, tmp_path):
        """Create a temporary CSV file with test data."""
        csv_path = tmp_path / "test_segments.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['segment_id', 'clone_density', 'perplexity'])
            # Write 1000 rows
            for i in range(1000):
                writer.writerow([f'segment_{i}', 0.5, 10.0])
        return csv_path

    @pytest.fixture
    def small_csv_file(self, tmp_path):
        """Create a temporary CSV file with few segments."""
        csv_path = tmp_path / "small_segments.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['segment_id', 'clone_density', 'perplexity'])
            # Write 50 rows
            for i in range(50):
                writer.writerow([f'segment_{i}', 0.5, 10.0])
        return csv_path

    def test_validate_segment_count_success(self, temp_csv_file):
        """Test validation passes when segment count meets threshold."""
        result = validate_segment_count(temp_csv_file, min_segments=500)
        assert result is True

    def test_validate_segment_count_failure(self, small_csv_file):
        """Test validation fails when segment count is below threshold."""
        result = validate_segment_count(small_csv_file, min_segments=100)
        assert result is False

    def test_validate_segment_count_file_not_found(self):
        """Test validation raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            validate_segment_count(Path('/nonexistent/file.csv'))

    def test_validate_segment_count_missing_column(self, temp_csv_file):
        """Test validation raises ValueError for missing segment_id column."""
        with pytest.raises(ValueError, match="Column 'segment_id' not found"):
            validate_segment_count(temp_csv_file, segment_id_column='wrong_column')

    def test_validate_segment_count_empty_file(self, tmp_path):
        """Test validation handles empty CSV files."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("segment_id,clone_density\n")
        
        result = validate_segment_count(empty_csv, min_segments=10)
        assert result is False

    def test_validate_segment_count_unique_segments(self, tmp_path):
        """Test that duplicate segment IDs are counted correctly."""
        csv_path = tmp_path / "duplicates.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['segment_id', 'value'])
            # Write 100 rows but only 5 unique segment IDs
            for i in range(100):
                writer.writerow([f'segment_{i % 5}', 0.5])
        
        # Should count 5 unique segments
        result = validate_segment_count(csv_path, min_segments=5)
        assert result is True
        
        result = validate_segment_count(csv_path, min_segments=6)
        assert result is False

    @patch('segment_count_validator.get_min_valid_segments')
    @patch('segment_count_validator.get_processed_dir')
    @patch('segment_count_validator.get_data_root')
    def test_validate_all_required_files(
        self, mock_data_root, mock_processed_dir, mock_min_segments, temp_csv_file
    ):
        """Test validation of all required files."""
        # Mock config functions
        mock_min_segments.return_value = 500
        mock_processed_dir.return_value = temp_csv_file.parent
        mock_data_root.return_value = temp_csv_file.parent.parent
        
        # Create mock required files
        clone_metrics = temp_csv_file.parent / 'clone_metrics.csv'
        perplexity = temp_csv_file.parent / 'perplexity_scores.csv'
        bug_detection = temp_csv_file.parent / 'bug_detection_results.csv'
        
        # Copy temp file to required names
        import shutil
        shutil.copy(temp_csv_file, clone_metrics)
        shutil.copy(temp_csv_file, perplexity)
        shutil.copy(temp_csv_file, bug_detection)
        
        result = validate_all_required_files()
        assert result is True
        
        # Clean up
        clone_metrics.unlink()
        perplexity.unlink()
        bug_detection.unlink()

    def test_load_processed_csv(self, temp_csv_file):
        """Test CSV loading functionality."""
        data = load_processed_csv(temp_csv_file)
        assert len(data) == 1000
        assert 'segment_id' in data[0]
        assert 'clone_density' in data[0]
        assert 'perplexity' in data[0]
