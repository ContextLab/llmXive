"""
Unit tests for data schema validation.
Tests the Pydantic models defined in code/schemas.py.
"""
import pytest
from pydantic import ValidationError
from schemas import (
    MetaAnalysis,
    Subsample,
    StabilityMetric,
    validate_meta_analysis,
    validate_subsample,
    validate_stability_metric,
)


class TestMetaAnalysisSchema:
    """Tests for the MetaAnalysis Pydantic model and validator."""

    def test_valid_meta_analysis(self):
        """Test that a valid MetaAnalysis object can be created."""
        data = {
            "id": "test_001",
            "title": "Sample Meta-Analysis",
            "effect_sizes": [0.5, 0.6, 0.4],
            "standard_errors": [0.1, 0.12, 0.09],
            "study_count": 3,
        }
        result = validate_meta_analysis(data)
        assert result.id == "test_001"
        assert len(result.effect_sizes) == 3
        assert result.study_count == 3

    def test_invalid_meta_analysis_missing_fields(self):
        """Test that validation fails for missing required fields."""
        data = {
            "id": "test_001",
            # Missing title, effect_sizes, etc.
        }
        with pytest.raises(ValidationError):
            validate_meta_analysis(data)

    def test_effect_sizes_and_se_must_match_length(self):
        """Test that effect_sizes and standard_errors must have the same length."""
        data = {
            "id": "test_002",
            "title": "Mismatched Lengths",
            "effect_sizes": [0.5, 0.6],
            "standard_errors": [0.1],  # Length mismatch
            "study_count": 2,
        }
        with pytest.raises(ValidationError):
            validate_meta_analysis(data)

    def test_study_count_consistency(self):
        """Test that study_count must match the length of effect_sizes."""
        data = {
            "id": "test_003",
            "title": "Count Mismatch",
            "effect_sizes": [0.5, 0.6, 0.4],
            "standard_errors": [0.1, 0.12, 0.09],
            "study_count": 5,  # Does not match length of 3
        }
        with pytest.raises(ValidationError):
            validate_meta_analysis(data)

    def test_empty_effect_sizes(self):
        """Test that empty effect_sizes list raises validation error."""
        data = {
            "id": "test_004",
            "title": "Empty Data",
            "effect_sizes": [],
            "standard_errors": [],
            "study_count": 0,
        }
        # Depending on schema strictness, this might be allowed or rejected.
        # Assuming minimum 1 study is required for meta-analysis context.
        with pytest.raises(ValidationError):
            validate_meta_analysis(data)


class TestSubsampleSchema:
    """Tests for the Subsample Pydantic model."""

    def test_valid_subsample(self):
        """Test that a valid Subsample object can be created."""
        data = {
            "meta_id": "test_001",
            "k": 3,
            "seed": 42,
            "effect_sizes": [0.5, 0.6, 0.4],
            "standard_errors": [0.1, 0.12, 0.09],
        }
        result = Subsample(**data)
        assert result.meta_id == "test_001"
        assert result.k == 3
        assert len(result.effect_sizes) == 3

    def test_invalid_subsample_missing_fields(self):
        """Test that validation fails for missing required fields."""
        data = {
            "meta_id": "test_001",
            # Missing k, seed, etc.
        }
        with pytest.raises(ValidationError):
            Subsample(**data)

    def test_k_must_be_positive(self):
        """Test that k must be a positive integer."""
        data = {
            "meta_id": "test_001",
            "k": 0,
            "seed": 42,
            "effect_sizes": [0.5],
            "standard_errors": [0.1],
        }
        with pytest.raises(ValidationError):
            Subsample(**data)

    def test_list_length_mismatch(self):
        """Test that effect_sizes and standard_errors must match length k."""
        data = {
            "meta_id": "test_001",
            "k": 3,
            "seed": 42,
            "effect_sizes": [0.5, 0.6],  # Length 2 != k
            "standard_errors": [0.1, 0.12, 0.09],
        }
        with pytest.raises(ValidationError):
            Subsample(**data)


class TestStabilityMetricSchema:
    """Tests for the StabilityMetric Pydantic model."""

    def test_stability_metric_creation(self):
        """Test that a StabilityMetric object can be created."""
        data = {
            "meta_id": "test_001",
            "k": 3,
            "model_type": "REML",
            "sd_effects": 0.05,
            "coverage_rate": 0.95,
        }
        result = StabilityMetric(**data)
        assert result.model_type == "REML"
        assert result.sd_effects == 0.05
        assert result.coverage_rate == 0.95

    def test_invalid_coverage_rate(self):
        """Test that coverage_rate must be between 0 and 1."""
        data = {
            "meta_id": "test_001",
            "k": 3,
            "model_type": "REML",
            "sd_effects": 0.05,
            "coverage_rate": 1.5,  # Invalid
        }
        with pytest.raises(ValidationError):
            StabilityMetric(**data)

    def test_negative_sd_effects(self):
        """Test that sd_effects cannot be negative."""
        data = {
            "meta_id": "test_001",
            "k": 3,
            "model_type": "REML",
            "sd_effects": -0.05,
            "coverage_rate": 0.95,
        }
        with pytest.raises(ValidationError):
            StabilityMetric(**data)