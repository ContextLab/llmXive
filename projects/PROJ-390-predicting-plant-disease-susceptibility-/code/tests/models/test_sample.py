"""
Tests for the Sample data model.
"""
import pytest
from src.models.sample import Sample, Species
from src.models.feature import Feature, FeatureType


class TestSampleCreation:
    """Tests for Sample instantiation and basic attributes."""

    def test_create_sample_minimal(self):
        """Test creating a sample with only required fields."""
        sample = Sample(
            sample_id="SRR123456",
            species=Species.WHEAT
        )
        assert sample.sample_id == "SRR123456"
        assert sample.species == Species.WHEAT
        assert sample.genomic_features == {}
        assert sample.environmental_features == {}
        assert sample.disease_status is None

    def test_create_sample_full(self):
        """Test creating a sample with all fields populated."""
        sample = Sample(
            sample_id="SRR789012",
            species=Species.RICE,
            genomic_features={"snp_001": 0.5, "snp_002": 1.0},
            environmental_features={"temp": 25.5, "humidity": 80.0},
            disease_status=1,
            latitude=35.6892,
            longitude=139.6917,
            collection_date="2023-05-15",
            phenotype_source="field-trial-db"
        )
        assert sample.sample_id == "SRR789012"
        assert sample.species == Species.RICE
        assert sample.genomic_features["snp_001"] == 0.5
        assert sample.environmental_features["temp"] == 25.5
        assert sample.disease_status == 1
        assert sample.latitude == 35.6892
        assert sample.phenotype_source == "field-trial-db"

    def test_invalid_species(self):
        """Test that creating a sample with an invalid species raises an error."""
        with pytest.raises(ValueError):
            Sample(sample_id="SRR000", species="invalid_species")  # type: ignore

    def test_unsupported_species_from_dict(self):
        """Test that from_dict raises error for unsupported species string."""
        with pytest.raises(ValueError):
            Sample.from_dict({
                "sample_id": "SRR000",
                "species": "unknown_plant"
            })


class TestSampleMethods:
    """Tests for Sample helper methods."""

    def test_to_dict_roundtrip(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = Sample(
            sample_id="SRR111",
            species=Species.MAIZE,
            genomic_features={"A": 0.1},
            disease_status=0
        )
        data = original.to_dict()
        restored = Sample.from_dict(data)

        assert restored.sample_id == original.sample_id
        assert restored.species == original.species
        assert restored.genomic_features == original.genomic_features
        assert restored.disease_status == original.disease_status

    def test_has_valid_label_true(self):
        """Test has_valid_label returns True for valid labels."""
        assert Sample("S1", Species.WHEAT, disease_status=1).has_valid_label()
        assert Sample("S2", Species.WHEAT, disease_status=0).has_valid_label()

    def test_has_valid_label_false(self):
        """Test has_valid_label returns False for missing or invalid labels."""
        assert not Sample("S3", Species.WHEAT).has_valid_label()
        assert not Sample("S4", Species.WHEAT, disease_status=2).has_valid_label()
        assert not Sample("S5", Species.WHEAT, disease_status=-1).has_valid_label()

    def test_has_coordinates_true(self):
        """Test has_coordinates returns True when lat/lon exist."""
        s = Sample("S1", Species.WHEAT, latitude=10.0, longitude=20.0)
        assert s.has_coordinates()

    def test_has_coordinates_false(self):
        """Test has_coordinates returns False if lat or lon is missing."""
        s1 = Sample("S1", Species.WHEAT, latitude=10.0)
        assert not s1.has_coordinates()
        s2 = Sample("S2", Species.WHEAT, longitude=20.0)
        assert not s2.has_coordinates()
        s3 = Sample("S3", Species.WHEAT)
        assert not s3.has_coordinates()
