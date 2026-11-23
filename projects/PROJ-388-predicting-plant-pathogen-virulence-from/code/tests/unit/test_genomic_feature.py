"""
Unit tests for the GenomicFeature model.
"""

import pytest
from src.models.genomic_feature import GenomicFeature


class TestGenomicFeature:
    """Test suite for GenomicFeature dataclass."""

    def test_create_valid_feature(self):
        """Test creation of a valid GenomicFeature instance."""
        feature = GenomicFeature(
            feature_id="PHI-12345",
            type="gene",
            presence_binary=True,
            pwm_count=3,
            source="PHI-base"
        )
        assert feature.feature_id == "PHI-12345"
        assert feature.type == "gene"
        assert feature.presence_binary is True
        assert feature.pwm_count == 3
        assert feature.source == "PHI-base"
        assert feature.metadata == {}

    def test_create_with_metadata(self):
        """Test creation with custom metadata."""
        feature = GenomicFeature(
            feature_id="MOTIF-001",
            type="TF_binding_site",
            presence_binary=False,
            pwm_count=0,
            source="custom_scan",
            metadata={"score": 0.85, "position": 1024}
        )
        assert feature.metadata["score"] == 0.85
        assert feature.metadata["position"] == 1024

    def test_empty_feature_id_raises_error(self):
        """Test that empty feature_id raises ValueError."""
        with pytest.raises(ValueError, match="feature_id cannot be empty"):
            GenomicFeature(
                feature_id="",
                type="gene",
                presence_binary=True,
                pwm_count=1,
                source="test"
            )

    def test_negative_pwm_count_raises_error(self):
        """Test that negative pwm_count raises ValueError."""
        with pytest.raises(ValueError, match="pwm_count cannot be negative"):
            GenomicFeature(
                feature_id="TEST-001",
                type="gene",
                presence_binary=True,
                pwm_count=-1,
                source="test"
            )

    def test_non_bool_presence_binary_raises_error(self):
        """Test that non-boolean presence_binary raises TypeError."""
        with pytest.raises(TypeError, match="presence_binary must be a boolean"):
            GenomicFeature(
                feature_id="TEST-001",
                type="gene",
                presence_binary="true",  # type: ignore
                pwm_count=1,
                source="test"
            )