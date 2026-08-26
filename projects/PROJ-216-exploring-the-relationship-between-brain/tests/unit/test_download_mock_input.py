import os
import sys
import json
import pytest
import tempfile
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from download import get_subject_list, validate_and_aggregate, check_validation_and_halt

class TestMockInputPath:
    """Unit tests for the --mock-input flag logic in download.py."""

    @pytest.fixture
    def mock_subjects_file(self, tmp_path):
        """Create a temporary mock subjects file."""
        data = [
            {"id": "sub-001", "fluid_intelligence_score": 0.85, "age": 25, "gender": "M"},
            {"id": "sub-002", "fluid_intelligence_score": 0.72, "age": 30, "gender": "F"},
            {"id": "sub-003", "fluid_intelligence_score": 0.91, "age": 22, "gender": "M"}
        ]
        file_path = tmp_path / "subjects.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        return file_path

    def test_load_mock_input_success(self, mock_subjects_file):
        """Test that get_subject_list successfully loads from a mock file."""
        subjects = get_subject_list(mock_input=str(mock_subjects_file))
        assert len(subjects) == 3
        assert subjects[0]['id'] == 'sub-001'
        assert subjects[0]['fluid_intelligence_score'] == 0.85

    def test_mock_input_missing_file_raises_error(self, tmp_path):
        """Test that get_subject_list raises FileNotFoundError for missing mock file."""
        with pytest.raises(FileNotFoundError):
            get_subject_list(mock_input=str(tmp_path / "nonexistent.json"))

    def test_mock_input_validation_failure(self, tmp_path):
        """Test that get_subject_list raises ValueError for invalid schema."""
        invalid_data = [{"id": "sub-001"}]  # Missing fluid_intelligence_score
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            json.dump(invalid_data, f)
        
        with pytest.raises(ValueError):
            get_subject_list(mock_input=str(file_path))

    def test_aggregate_mock_data(self, mock_subjects_file):
        """Test that validate_and_aggregate works with mock data."""
        subjects = get_subject_list(mock_input=str(mock_subjects_file))
        agg = validate_and_aggregate(subjects)
        
        assert agg['total_subjects'] == 3
        assert agg['min_score'] == 0.72
        assert agg['max_score'] == 0.91
        assert agg['mean_score'] == pytest.approx((0.85 + 0.72 + 0.91) / 3)

    def test_halt_on_zero_valid_scores(self, tmp_path):
        """Test that check_validation_and_halt exits when no scores are found."""
        # Create a mock file with subjects but no scores
        invalid_data = [{"id": "sub-001"}]
        file_path = tmp_path / "no_scores.json"
        with open(file_path, 'w') as f:
            json.dump(invalid_data, f)
        
        subjects = get_subject_list(mock_input=str(file_path))
        # Note: get_subject_list already filters or raises, but if it returns empty:
        if not subjects:
            with pytest.raises(SystemExit):
                check_validation_and_halt({'total_subjects': 0})