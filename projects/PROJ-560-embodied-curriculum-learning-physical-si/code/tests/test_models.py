import pytest
from typing import Dict, Any
from src.models import DatasetRecord

class TestDatasetRecordValidation:
    """Unit tests for DatasetRecord validation logic."""

    def test_valid_record_creation(self):
        """Test that a valid DatasetRecord can be created."""
        record = DatasetRecord(
            pre_test_score=85.0,
            post_test_score=92.0,
            instruction_type="embodied",
            covariates={"age": 12, "gender": "M"}
        )
        assert record.pre_test_score == 85.0
        assert record.post_test_score == 92.0
        assert record.instruction_type == "embodied"
        assert record.covariates == {"age": 12, "gender": "M"}

    def test_missing_required_field_pre_test(self):
        """Test that missing pre_test_score raises TypeError."""
        with pytest.raises(TypeError):
            DatasetRecord(
                post_test_score=92.0,
                instruction_type="embodied",
                covariates={}
            )

    def test_missing_required_field_post_test(self):
        """Test that missing post_test_score raises TypeError."""
        with pytest.raises(TypeError):
            DatasetRecord(
                pre_test_score=85.0,
                instruction_type="embodied",
                covariates={}
            )

    def test_missing_required_field_instruction_type(self):
        """Test that missing instruction_type raises TypeError."""
        with pytest.raises(TypeError):
            DatasetRecord(
                pre_test_score=85.0,
                post_test_score=92.0,
                covariates={}
            )

    def test_negative_scores_allowed(self):
        """Test that negative scores are allowed (data integrity check)."""
        record = DatasetRecord(
            pre_test_score=-5.0,
            post_test_score=-2.0,
            instruction_type="static",
            covariates={}
        )
        assert record.pre_test_score == -5.0
        assert record.post_test_score == -2.0

    def test_empty_covariates_allowed(self):
        """Test that empty covariates dict is valid."""
        record = DatasetRecord(
            pre_test_score=80.0,
            post_test_score=85.0,
            instruction_type="embodied",
            covariates={}
        )
        assert record.covariates == {}

    def test_covariates_type_check(self):
        """Test that covariates must be a dictionary."""
        with pytest.raises(TypeError):
            DatasetRecord(
                pre_test_score=80.0,
                post_test_score=85.0,
                instruction_type="embodied",
                covariates="invalid_type"
            )

    def test_gain_score_calculation_property(self):
        """Test that gain_score can be calculated correctly."""
        record = DatasetRecord(
            pre_test_score=60.0,
            post_test_score=75.0,
            instruction_type="embodied",
            covariates={}
        )
        gain = record.post_test_score - record.pre_test_score
        assert gain == 15.0

    def test_string_instruction_type(self):
        """Test that instruction_type must be a string."""
        with pytest.raises(TypeError):
            DatasetRecord(
                pre_test_score=80.0,
                post_test_score=85.0,
                instruction_type=123,
                covariates={}
            )