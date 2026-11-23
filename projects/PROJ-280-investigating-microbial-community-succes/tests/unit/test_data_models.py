"""
Unit tests for data_models.py.

Verifies Sample, Taxon, and FeatureTable classes function correctly
and align with the expected schema.
"""

import pytest
from code.data_models import Sample, Taxon, FeatureTable, SampleStage


class TestSample:
    def test_sample_creation(self):
        """Test basic sample creation."""
        sample = Sample(
            sample_id="S001",
            dataset_id="D001",
            stage=SampleStage.EARLY,
            read_depth=10000,
            metadata={"N_removal_rate": 0.8},
            raw_feature_counts={"T001": 500, "T002": 300}
        )
        
        assert sample.sample_id == "S001"
        assert sample.stage == SampleStage.EARLY
        assert sample.read_depth == 10000
        assert sample.get_nutrient_removal_rate("N") == 0.8
        assert sample.get_nutrient_removal_rate("P") is None

    def test_sample_from_dict(self):
        """Test Sample creation from dictionary."""
        data = {
            "sample_id": "S002",
            "dataset_id": "D002",
            "stage": "mature",
            "read_depth": 5000,
            "metadata": {"P_removal_rate": 0.5},
            "raw_feature_counts": {"T003": 100}
        }
        sample = Sample.from_dict(data)
        
        assert sample.sample_id == "S002"
        assert sample.stage == SampleStage.MATURE
        assert sample.get_nutrient_removal_rate("P") == 0.5

    def test_sample_to_dict(self):
        """Test Sample serialization."""
        sample = Sample(
            sample_id="S003",
            dataset_id="D003",
            stage=SampleStage.MIDDLE,
            read_depth=8000
        )
        d = sample.to_dict()
        
        assert d["sample_id"] == "S003"
        assert d["stage"] == "middle"
        assert d["read_depth"] == 8000

    def test_unknown_stage(self):
        """Test handling of unknown stage."""
        data = {
            "sample_id": "S004",
            "dataset_id": "D004",
            "stage": "invalid_stage",
            "read_depth": 1000
        }
        sample = Sample.from_dict(data)
        assert sample.stage == SampleStage.UNKNOWN


class TestTaxon:
    def test_taxon_creation(self):
        """Test basic taxon creation."""
        taxon = Taxon(
            taxon_id="T001",
            taxonomy="k__Bacteria;p__Proteobacteria",
            abundance={"S001": 500, "S002": 200},
            total_abundance=700
        )
        
        assert taxon.taxon_id == "T001"
        assert taxon.get_abundance_in_sample("S001") == 500
        assert taxon.get_abundance_in_sample("S003") == 0

    def test_relative_abundance(self):
        """Test relative abundance calculation."""
        taxon = Taxon(
            taxon_id="T002",
            abundance={"S001": 500}
        )
        
        # Depth = 10000
        rel_abund = taxon.relative_abundance_in_sample("S001", 10000)
        assert rel_abund == 0.05
        
        # Zero depth
        rel_abund_zero = taxon.relative_abundance_in_sample("S001", 0)
        assert rel_abund_zero == 0.0

    def test_taxon_from_dict(self):
        """Test Taxon creation from dictionary."""
        data = {
            "taxon_id": "T003",
            "taxonomy": "k__Bacteria",
            "abundance": {"S001": 100, "S002": 200},
            "total_abundance": 300
        }
        taxon = Taxon.from_dict(data)
        
        assert taxon.taxon_id == "T003"
        assert taxon.total_abundance == 300


class TestFeatureTable:
    def test_feature_table_creation(self):
        """Test basic FeatureTable creation."""
        sample = Sample(
            sample_id="S001",
            dataset_id="D001",
            stage=SampleStage.EARLY,
            read_depth=1000
        )
        taxon = Taxon(taxon_id="T001", abundance={"S001": 500})
        
        table = FeatureTable(samples=[sample], taxa=[taxon])
        
        assert len(table.samples) == 1
        assert len(table.taxa) == 1

    def test_get_sample(self):
        """Test retrieving samples by ID."""
        sample = Sample(
            sample_id="S001",
            dataset_id="D001",
            stage=SampleStage.EARLY,
            read_depth=1000
        )
        table = FeatureTable(samples=[sample])
        
        assert table.get_sample("S001") == sample
        assert table.get_sample("NONEXISTENT") is None

    def test_get_taxon(self):
        """Test retrieving taxa by ID."""
        taxon = Taxon(taxon_id="T001")
        table = FeatureTable(taxa=[taxon])
        
        assert table.get_taxon("T001") == taxon
        assert table.get_taxon("NONEXISTENT") is None

    def test_roundtrip_serialization(self):
        """Test that FeatureTable can be serialized and deserialized."""
        sample = Sample(
            sample_id="S001",
            dataset_id="D001",
            stage=SampleStage.MATURE,
            read_depth=5000,
            metadata={"N_removal_rate": 0.9}
        )
        taxon = Taxon(
            taxon_id="T001",
            taxonomy="k__Bacteria",
            abundance={"S001": 1000},
            total_abundance=1000
        )
        
        original = FeatureTable(samples=[sample], taxa=[taxon], metadata={"version": "1.0"})
        data = original.to_dict()
        restored = FeatureTable.from_dict(data)
        
        assert restored.samples[0].sample_id == "S001"
        assert restored.samples[0].stage == SampleStage.MATURE
        assert restored.taxa[0].taxon_id == "T001"
        assert restored.metadata["version"] == "1.0"