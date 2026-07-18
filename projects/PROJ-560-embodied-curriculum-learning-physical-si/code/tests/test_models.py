"""
Tests for the models module.
"""
import pytest
from typing import Dict, Any
from src.models import DatasetRecord


class TestDatasetRecordValidation:
    """Test cases for DatasetRecord validation and functionality."""

    def test_create_valid_record(self):
        """Test creating a valid DatasetRecord."""
        record = DatasetRecord(
            pre_test_score=50.0,
            post_test_score=60.0,
            instruction_type="embodied",
            covariates={"age": 10}
        )
        assert record.pre_test_score == 50.0
        assert record.post_test_score == 60.0
        assert record.instruction_type == "embodied"
        assert record.covariates["age"] == 10

    def test_to_dict(self):
        """Test converting record to dictionary."""
        record = DatasetRecord(
            pre_test_score=50.0,
            post_test_score=60.0,
            instruction_type="static",
            covariates={}
        )
        data = record.to_dict()
        assert data["pre_test_score"] == 50.0
        assert data["post_test_score"] == 60.0
        assert data["instruction_type"] == "static"
        assert "covariates" in data
