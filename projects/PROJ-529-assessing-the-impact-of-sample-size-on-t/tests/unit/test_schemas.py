"""
Contract test for data schema validation (US1).
Tests the Pydantic schemas defined in code/schemas.py to ensure
they correctly validate real-world data structures and reject invalid inputs.
"""
import pytest
from datetime import datetime
import math

# Import schemas from the project code
from schemas import (
    StudySchema,
    SubsampleSchema,
    MetaAnalysisSchema,
    StabilityMetricSchema
)
from utils.exceptions import DataValidationError


class TestStudySchema:
    """Tests for the Study entity schema."""

    def test_valid_study(self):
        """Test that a valid study passes validation."""
        data = {
            "study_id": "STUDY-001",
            "meta_analysis_id": "META-001",
            "effect_size": 0.45,
            "standard_error": 0.12,
            "sample_size": 150,
            "year": 2021,
            "source": "Cochrane"
        }
        study = StudySchema(**data)
        assert study.study_id == "STUDY-001"
        assert study.effect_size == 0.45
        assert study.standard_error == 0.12

    def test_invalid_negative_se(self):
        """Test that negative standard error is rejected."""
        data = {
            "study_id": "STUDY-002",
            "meta_analysis_id": "META-001",
            "effect_size": 0.3,
            "standard_error": -0.05,
            "sample_size": 100,
            "year": 2020,
            "source": "Campbell"
        }
        with pytest.raises(ValueError):
            StudySchema(**data)

    def test_invalid_zero_sample_size(self):
        """Test that zero sample size is rejected."""
        data = {
            "study_id": "STUDY-003",
            "meta_analysis_id": "META-001",
            "effect_size": 0.2,
            "standard_error": 0.1,
            "sample_size": 0,
            "year": 2019,
            "source": "Cochrane"
        }
        with pytest.raises(ValueError):
            StudySchema(**data)

    def test_valid_zero_se(self):
        """Test that zero standard error is allowed (handled by error handling logic later)."""
        data = {
            "study_id": "STUDY-004",
            "meta_analysis_id": "META-001",
            "effect_size": 0.5,
            "standard_error": 0.0,
            "sample_size": 200,
            "year": 2022,
            "source": "Cochrane"
        }
        study = StudySchema(**data)
        assert study.standard_error == 0.0


class TestSubsampleSchema:
    """Tests for the Subsample entity schema."""

    def test_valid_subsample(self):
        """Test that a valid subsample passes validation."""
        data = {
            "subsample_id": "SUB-001",
            "meta_analysis_id": "META-001",
            "k": 5,
            "seed": 42,
            "effect_size": 0.42,
            "standard_error": 0.15,
            "estimator_type": "REML",
            "study_ids": ["STUDY-001", "STUDY-002", "STUDY-003", "STUDY-004", "STUDY-005"]
        }
        subsample = SubsampleSchema(**data)
        assert subsample.k == 5
        assert subsample.seed == 42
        assert len(subsample.study_ids) == 5

    def test_invalid_k_less_than_3(self):
        """Test that k < 3 is rejected."""
        data = {
            "subsample_id": "SUB-002",
            "meta_analysis_id": "META-001",
            "k": 2,
            "seed": 43,
            "effect_size": 0.3,
            "standard_error": 0.1,
            "estimator_type": "DL",
            "study_ids": ["STUDY-001", "STUDY-002"]
        }
        with pytest.raises(ValueError):
            SubsampleSchema(**data)

    def test_invalid_mismatched_k_and_studies(self):
        """Test that k must match the length of study_ids."""
        data = {
            "subsample_id": "SUB-003",
            "meta_analysis_id": "META-001",
            "k": 5,
            "seed": 44,
            "effect_size": 0.35,
            "standard_error": 0.12,
            "estimator_type": "DL",
            "study_ids": ["STUDY-001", "STUDY-002"]  # k=5 but only 2 IDs
        }
        with pytest.raises(ValueError):
            SubsampleSchema(**data)


class TestMetaAnalysisSchema:
    """Tests for the MetaAnalysis entity schema."""

    def test_valid_meta_analysis(self):
        """Test that a valid meta-analysis passes validation."""
        data = {
            "meta_analysis_id": "META-001",
            "title": "Impact of Sample Size on Reliability",
            "source": "Cochrane",
            "year": 2023,
            "total_studies": 25,
            "pooled_effect": 0.35,
            "pooled_se": 0.08,
            "model_type": "REML"
        }
        meta = MetaAnalysisSchema(**data)
        assert meta.meta_analysis_id == "META-001"
        assert meta.total_studies == 25

    def test_invalid_total_studies_zero(self):
        """Test that total_studies must be positive."""
        data = {
            "meta_analysis_id": "META-002",
            "title": "Invalid Meta",
            "source": "Cochrane",
            "year": 2023,
            "total_studies": 0,
            "pooled_effect": 0.3,
            "pooled_se": 0.1,
            "model_type": "FE"
        }
        with pytest.raises(ValueError):
            MetaAnalysisSchema(**data)


class TestStabilityMetricSchema:
    """Tests for the StabilityMetric entity schema."""

    def test_valid_stability_metric(self):
        """Test that a valid stability metric passes validation."""
        data = {
            "meta_analysis_id": "META-001",
            "k": 10,
            "sd_effects": 0.12,
            "coverage_rate": 0.95,
            "model_type": "REML",
            "changepoint_detected": False
        }
        metric = StabilityMetricSchema(**data)
        assert metric.k == 10
        assert metric.sd_effects == 0.12
        assert metric.coverage_rate == 0.95

    def test_invalid_coverage_rate_out_of_bounds(self):
        """Test that coverage_rate must be between 0 and 1."""
        data = {
            "meta_analysis_id": "META-001",
            "k": 10,
            "sd_effects": 0.12,
            "coverage_rate": 1.5,
            "model_type": "REML",
            "changepoint_detected": False
        }
        with pytest.raises(ValueError):
            StabilityMetricSchema(**data)

    def test_invalid_negative_sd(self):
        """Test that sd_effects cannot be negative."""
        data = {
            "meta_analysis_id": "META-001",
            "k": 10,
            "sd_effects": -0.05,
            "coverage_rate": 0.95,
            "model_type": "REML",
            "changepoint_detected": False
        }
        with pytest.raises(ValueError):
            StabilityMetricSchema(**data)