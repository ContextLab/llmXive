"""
Unit tests for the Subject and BehavioralScore models.
"""
import pytest
from code.models import Subject, BehavioralScore


class TestSubject:
    def test_create_subject_valid(self):
        """Test creation of a valid Subject."""
        sub = Subject(id="sub-001", age=25, gender="M")
        assert sub.id == "sub-001"
        assert sub.age == 25
        assert sub.gender == "M"
        assert sub.raw_fMRI_path is None

    def test_create_subject_minimal(self):
        """Test creation of a Subject with only ID."""
        sub = Subject(id="sub-002")
        assert sub.id == "sub-002"
        assert sub.age is None
        assert sub.gender is None

    def test_create_subject_invalid_id(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Subject ID cannot be empty."):
            Subject(id="")

    def test_set_file_paths(self):
        """Test setting file paths."""
        sub = Subject(id="sub-003")
        sub.raw_fMRI_path = "data/raw/sub-003.nii.gz"
        sub.preprocessed_fMRI_path = "data/processed/sub-003.nii.gz"
        assert sub.raw_fMRI_path == "data/raw/sub-003.nii.gz"


class TestBehavioralScore:
    def test_create_score_valid(self):
        """Test creation of a valid BehavioralScore."""
        score = BehavioralScore(
            subject_id="sub-001",
            score_value=85.5,
            source_type="fluid_intelligence"
        )
        assert score.subject_id == "sub-001"
        assert score.score_value == 85.5
        assert score.source_type == "fluid_intelligence"
        assert score.source_file is None
        assert score.metadata == {}

    def test_create_score_with_metadata(self):
        """Test creation of a score with metadata."""
        score = BehavioralScore(
            subject_id="sub-002",
            score_value=90.0,
            source_type="creativity_score",
            metadata={"test_id": "T001", "session": 1}
        )
        assert score.metadata["test_id"] == "T001"
        assert score.metadata["session"] == 1

    def test_create_score_invalid_subject_id(self):
        """Test that empty subject_id raises ValueError."""
        with pytest.raises(ValueError, match="Subject ID cannot be empty."):
            BehavioralScore(
                subject_id="",
                score_value=50.0,
                source_type="test"
            )

    def test_create_score_invalid_value(self):
        """Test that None score_value raises ValueError."""
        with pytest.raises(ValueError, match="Score value cannot be None."):
            BehavioralScore(
                subject_id="sub-001",
                score_value=None,
                source_type="test"
            )

    def test_create_score_invalid_source_type(self):
        """Test that empty source_type raises ValueError."""
        with pytest.raises(ValueError, match="Source type cannot be empty."):
            BehavioralScore(
                subject_id="sub-001",
                score_value=50.0,
                source_type=""
            )
