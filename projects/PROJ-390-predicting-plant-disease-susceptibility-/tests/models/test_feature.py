"""
Tests for the Feature data model.
"""
import pytest
from src.models.feature import Feature, FeatureType


class TestFeatureCreation:
    def test_create_genomic_feature(self):
        """Test creation of a genomic feature."""
        feature = Feature(
            feature_id="rs12345",
            feature_type=FeatureType.SNP_FREQUENCY,
            value=0.33
        )
        assert feature.feature_id == "rs12345"
        assert feature.feature_type == FeatureType.SNP_FREQUENCY
        assert feature.value == 0.33
        assert feature.is_genomic()

    def test_create_environmental_feature(self):
        """Test creation of an environmental feature."""
        feature = Feature(
            feature_id="temp_avg",
            feature_type=FeatureType.TEMPERATURE,
            value=28.5
        )
        assert feature.is_environmental()
        assert not feature.is_genomic()

    def test_invalid_value_type(self):
        """Test that non-numeric values raise an error."""
        with pytest.raises(ValueError):
            Feature(
                feature_id="bad",
                feature_type=FeatureType.TEMPERATURE,
                value="not_a_number"
            )


class TestFeatureMethods:
    def test_is_genomic(self):
        """Test genomic classification."""
        snp = Feature("rs1", FeatureType.SNP_FREQUENCY, 0.5)
        expr = Feature("gene1", FeatureType.GENE_EXPRESSION, 10.2)
        assert snp.is_genomic()
        assert expr.is_genomic()

    def test_is_environmental(self):
        """Test environmental classification."""
        temp = Feature("t1", FeatureType.TEMPERATURE, 20.0)
        hum = Feature("h1", FeatureType.HUMIDITY, 0.6)
        assert temp.is_environmental()
        assert hum.is_environmental()

    def test_other_type(self):
        """Test that 'other' type is neither genomic nor environmental."""
        feat = Feature("misc", FeatureType.OTHER, 1.0)
        assert not feat.is_genomic()
        assert not feat.is_environmental()
