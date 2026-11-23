"""
Tests for the Feature data model.
"""
import pytest
from src.models.feature import Feature, FeatureType


class TestFeatureCreation:
    """Tests for Feature instantiation."""

    def test_create_feature_genomic(self):
        """Test creating a genomic feature."""
        f = Feature(
            name="snp_chr1_10023",
            feature_type=FeatureType.GENOMIC,
            source="NCBI-SRA",
            description="SNP at position 10023 on chromosome 1"
        )
        assert f.name == "snp_chr1_10023"
        assert f.feature_type == FeatureType.GENOMIC
        assert f.source == "NCBI-SRA"

    def test_create_feature_environmental(self):
        """Test creating an environmental feature."""
        f = Feature(
            name="mean_temp_july",
            feature_type=FeatureType.ENVIRONMENTAL,
            source="ERA5-Land",
            unit="Celsius"
        )
        assert f.name == "mean_temp_july"
        assert f.feature_type == FeatureType.ENVIRONMENTAL
        assert f.unit == "Celsius"

    def test_invalid_feature_type(self):
        """Test that creating a feature with invalid type raises error."""
        with pytest.raises(ValueError):
            Feature(name="x", feature_type="invalid")  # type: ignore

    def test_unsupported_type_from_dict(self):
        """Test that from_dict raises error for unsupported feature type."""
        with pytest.raises(ValueError):
            Feature.from_dict({
                "name": "test",
                "feature_type": "unknown_type"
            })


class TestFeatureMethods:
    """Tests for Feature helper methods."""

    def test_to_dict_roundtrip(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = Feature(
            name="snp_test",
            feature_type=FeatureType.GENOMIC,
            source="TestSource",
            description="Test desc"
        )
        data = original.to_dict()
        restored = Feature.from_dict(data)

        assert restored.name == original.name
        assert restored.feature_type == original.feature_type
        assert restored.source == original.source
        assert restored.description == original.description
        assert restored.unit == original.unit
