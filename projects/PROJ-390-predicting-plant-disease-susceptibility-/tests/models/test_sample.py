"""
Tests for the Sample data model.
"""
import pytest
from src.models.sample import Sample, Species
from src.models.feature import Feature, FeatureType


class TestSampleCreation:
    def test_create_valid_sample(self):
        """Test creation of a valid sample."""
        sample = Sample(
            sample_id="S001",
            species=Species.WHEAT,
            accession_id="GCA_000003205.5",
            latitude=45.5,
            longitude=-75.0,
            collection_date="2023-05-01",
            disease_status=1,
            phenotype_source="field-trial-db"
        )
        assert sample.sample_id == "S001"
        assert sample.species == Species.WHEAT
        assert sample.is_valid()

    def test_create_sample_missing_required_fails(self):
        """Test that a sample missing required fields is invalid."""
        sample = Sample(
            sample_id="",  # Empty ID
            species=Species.WHEAT,
            accession_id="GCA_000003205.5",
            latitude=45.5,
            longitude=-75.0,
            collection_date="2023-05-01",
            disease_status=1,
            phenotype_source="field-trial-db"
        )
        assert not sample.is_valid()

    def test_invalid_disease_status(self):
        """Test that disease_status must be 0 or 1."""
        sample = Sample(
            sample_id="S002",
            species=Species.RICE,
            accession_id="GCA_001433935.2",
            latitude=35.0,
            longitude=139.0,
            collection_date="2023-06-15",
            disease_status=2,  # Invalid
            phenotype_source="field-trial-db"
        )
        assert not sample.is_valid()


class TestSampleMethods:
    def test_add_genomic_feature(self):
        """Test adding a genomic feature to a sample."""
        sample = Sample(
            sample_id="S003",
            species=Species.MAIZE,
            accession_id="GCA_000005005.4",
            latitude=40.0,
            longitude=-88.0,
            collection_date="2023-07-20",
            disease_status=0,
            phenotype_source="pathology-archive"
        )
        feature = Feature(
            feature_id="rs123",
            feature_type=FeatureType.SNP_FREQUENCY,
            value=0.45
        )
        sample.add_genomic_feature(feature)
        assert len(sample.genomic_features) == 1
        assert sample.genomic_features[0].value == 0.45

    def test_add_environmental_feature(self):
        """Test adding an environmental feature."""
        sample = Sample(
            sample_id="S004",
            species=Species.TOMATO,
            accession_id="GCA_000188115.5",
            latitude=34.0,
            longitude=-118.0,
            collection_date="2023-08-10",
            disease_status=1,
            phenotype_source="field-trial-db"
        )
        sample.add_environmental_feature("temp_mean", 25.5)
        assert sample.environmental_features["temp_mean"] == 25.5

    def test_get_feature_vector(self):
        """Test construction of feature vector."""
        sample = Sample(
            sample_id="S005",
            species=Species.SOYBEAN,
            accession_id="GCA_000004195.3",
            latitude=39.0,
            longitude=-77.0,
            collection_date="2023-09-05",
            disease_status=1,
            phenotype_source="field-trial-db"
        )
        sample.add_genomic_feature(Feature("rs1", FeatureType.SNP_FREQUENCY, 0.1))
        sample.add_genomic_feature(Feature("rs2", FeatureType.SNP_FREQUENCY, 0.9))
        sample.add_environmental_feature("humidity", 0.8)
        sample.add_environmental_feature("temp", 22.0)

        vector = sample.get_feature_vector()
        assert len(vector) == 4  # 2 genomic + 2 environmental
        assert vector[0] == 0.1
        assert vector[1] == 0.9
