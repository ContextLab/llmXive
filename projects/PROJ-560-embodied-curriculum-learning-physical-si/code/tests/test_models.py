"""
Unit Tests for Data Models in the Embodied Curriculum Learning Pipeline.

This module contains tests for the DatasetRecord, AnalysisResult, and
SensitivitySweep dataclasses to ensure they behave as expected.
"""
import pytest
from typing import Dict, Any
from src.models import DatasetRecord, AnalysisResult, SensitivitySweep


class TestDatasetRecordValidation:
    """Tests for DatasetRecord dataclass."""

    def test_create_record_with_required_fields(self):
        """Test creating a record with only required fields."""
        record = DatasetRecord(id="test_001")
        assert record.id == "test_001"
        assert record.pre_test_score is None
        assert record.post_test_score is None
        assert record.instruction_type is None
        assert record.covariates == {}
        assert record.gain_score is None

    def test_create_record_with_all_fields(self):
        """Test creating a record with all fields populated."""
        record = DatasetRecord(
            id="test_002",
            pre_test_score=50.0,
            post_test_score=55.0,
            instruction_type="embodied",
            covariates={"concept": "math", "age": 15}
        )
        assert record.id == "test_002"
        assert record.pre_test_score == 50.0
        assert record.post_test_score == 55.0
        assert record.instruction_type == "embodied"
        assert record.covariates == {"concept": "math", "age": 15}
        assert record.gain_score is None

    def test_gain_score_assignment(self):
        """Test assigning gain score to a record."""
        record = DatasetRecord(
            id="test_003",
            pre_test_score=50.0,
            post_test_score=55.0
        )
        record.gain_score = 5.0
        assert record.gain_score == 5.0

    def test_to_dict(self):
        """Test converting a record to a dictionary."""
        record = DatasetRecord(
            id="test_004",
            pre_test_score=50.0,
            post_test_score=55.0,
            instruction_type="static",
            covariates={"concept": "physics"}
        )
        record.gain_score = 5.0
        d = record.to_dict()
        assert d == {
            "id": "test_004",
            "pre_test_score": 50.0,
            "post_test_score": 55.0,
            "instruction_type": "static",
            "covariates": {"concept": "physics"},
            "gain_score": 5.0
        }

    def test_invalid_id_type(self):
        """Test that creating a record with invalid id type raises TypeError."""
        with pytest.raises(TypeError):
            DatasetRecord(id=12345)

    def test_invalid_score_type(self):
        """Test that creating a record with invalid score type raises TypeError."""
        with pytest.raises(TypeError):
            DatasetRecord(
                id="test_005",
                pre_test_score="fifty",
                post_test_score=55.0
            )

    def test_invalid_covariates_type(self):
        """Test that creating a record with invalid covariates type raises TypeError."""
        with pytest.raises(TypeError):
            DatasetRecord(
                id="test_006",
                pre_test_score=50.0,
                post_test_score=55.0,
                covariates=["concept", "math"]
            )


class TestAnalysisResultValidation:
    """Tests for AnalysisResult dataclass."""

    def test_create_analysis_result(self):
        """Test creating an AnalysisResult object."""
        result = AnalysisResult(
            concept_name="math_reasoning",
            t_statistic=2.5,
            p_value=0.01,
            effect_size=0.8,
            confidence_interval=(0.5, 1.1),
            bonferroni_adjusted_p=0.02,
            is_significant=True,
            power=0.9,
            underpowered=False,
            collinearity_detected=False,
            associational_framing="Test framing"
        )
        assert result.concept_name == "math_reasoning"
        assert result.t_statistic == 2.5
        assert result.is_significant is True

    def test_to_dict(self):
        """Test converting an AnalysisResult to a dictionary."""
        result = AnalysisResult(
            concept_name="test",
            t_statistic=1.0,
            p_value=0.05,
            effect_size=0.5,
            confidence_interval=(0.0, 1.0),
            bonferroni_adjusted_p=0.1,
            is_significant=False,
            power=0.7,
            underpowered=True,
            collinearity_detected=False,
            associational_framing="Framing text"
        )
        d = result.to_dict()
        assert d["concept_name"] == "test"
        assert d["is_significant"] is False
        assert d["underpowered"] is True

    def test_invalid_confidence_interval_length(self):
        """Test that creating a result with invalid CI length raises ValueError."""
        with pytest.raises(ValueError):
            AnalysisResult(
                concept_name="test",
                t_statistic=1.0,
                p_value=0.05,
                effect_size=0.5,
                confidence_interval=(0.0,),  # Invalid length
                bonferroni_adjusted_p=0.1,
                is_significant=False,
                power=0.7,
                underpowered=True,
                collinearity_detected=False,
                associational_framing="Framing text"
            )

    def test_negative_p_value(self):
        """Test that creating a result with negative p_value raises ValueError."""
        with pytest.raises(ValueError):
            AnalysisResult(
                concept_name="test",
                t_statistic=1.0,
                p_value=-0.05,
                effect_size=0.5,
                confidence_interval=(0.0, 1.0),
                bonferroni_adjusted_p=0.1,
                is_significant=False,
                power=0.7,
                underpowered=True,
                collinearity_detected=False,
                associational_framing="Framing text"
            )


class TestSensitivitySweepValidation:
    """Tests for SensitivitySweep dataclass."""

    def test_create_sensitivity_sweep(self):
        """Test creating a SensitivitySweep object."""
        sweep = SensitivitySweep(
            threshold=0.05,
            effect_size=0.6,
            is_significant=True,
            sample_size=100
        )
        assert sweep.threshold == 0.05
        assert sweep.effect_size == 0.6
        assert sweep.sample_size == 100

    def test_to_dict(self):
        """Test converting a SensitivitySweep to a dictionary."""
        sweep = SensitivitySweep(
            threshold=0.1,
            effect_size=0.4,
            is_significant=False,
            sample_size=50
        )
        d = sweep.to_dict()
        assert d == {
            "threshold": 0.1,
            "effect_size": 0.4,
            "is_significant": False,
            "sample_size": 50
        }

    def test_invalid_threshold_type(self):
        """Test that creating a sweep with invalid threshold type raises TypeError."""
        with pytest.raises(TypeError):
            SensitivitySweep(
                threshold="0.05",
                effect_size=0.6,
                is_significant=True,
                sample_size=100
            )

    def test_negative_sample_size(self):
        """Test that creating a sweep with negative sample_size raises ValueError."""
        with pytest.raises(ValueError):
            SensitivitySweep(
                threshold=0.05,
                effect_size=0.6,
                is_significant=True,
                sample_size=-10
            )