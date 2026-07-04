"""
Unit tests for the data models (Sample, Taxon) defined in code/utils/data_models.py.
"""

import pytest
from code.utils.data_models import Sample, Taxon, DataType


class TestTaxon:
    def test_taxon_creation(self):
        taxon = Taxon(id="g__Bacteroides", rank="genus", name="Bacteroides")
        assert taxon.id == "g__Bacteroides"
        assert taxon.rank == "genus"
        assert taxon.name == "Bacteroides"
        assert taxon.metadata == {}

    def test_taxon_to_dict(self):
        taxon = Taxon(id="g__Bacteroides", rank="genus", name="Bacteroides", metadata={"source": "AGP"})
        d = taxon.to_dict()
        assert d["id"] == "g__Bacteroides"
        assert d["rank"] == "genus"
        assert d["metadata"]["source"] == "AGP"

    def test_taxon_from_dict(self):
        data = {
            "id": "s__E_coli",
            "rank": "species",
            "name": "Escherichia coli",
            "metadata": {"pathogenic": True}
        }
        taxon = Taxon.from_dict(data)
        assert taxon.id == "s__E_coli"
        assert taxon.metadata["pathogenic"] is True


class TestSample:
    def test_sample_creation(self):
        sample = Sample(
            sample_id="S001",
            participant_id="P001",
            age=65,
            data_type=DataType.RAW_COUNTS
        )
        assert sample.sample_id == "S001"
        assert sample.age == 65
        assert sample.data_type == DataType.RAW_COUNTS

    def test_get_abundance(self):
        sample = Sample(
            sample_id="S001",
            participant_id="P001",
            taxon_abundances={"g__Bacteroides": 100.0, "g__Prevotella": 50.0}
        )
        assert sample.get_abundance("g__Bacteroides") == 100.0
        assert sample.get_abundance("g__Unknown") == 0.0

    def test_has_non_null_cognitive_score(self):
        # No scores
        sample = Sample(sample_id="S001", participant_id="P001")
        assert not sample.has_non_null_cognitive_score()

        # Valid score
        sample.cognitive_scores = {"memory": 0.8}
        assert sample.has_non_null_cognitive_score()

        # Null/NaN score
        sample.cognitive_scores = {"memory": None}
        assert not sample.has_non_null_cognitive_score()

    def test_filter_by_age(self):
        young = Sample(sample_id="S001", participant_id="P001", age=45)
        old = Sample(sample_id="S002", participant_id="P002", age=70)
        no_age = Sample(sample_id="S003", participant_id="P003")

        assert not young.filter_by_age(60)
        assert old.filter_by_age(60)
        assert not no_age.filter_by_age(60)

    def test_serialization_roundtrip(self):
        original = Sample(
            sample_id="S001",
            participant_id="P001",
            age=62,
            cognitive_scores={"executive": 0.9},
            taxon_abundances={"g__Firmicutes": 500.0},
            data_type=DataType.RELATIVE_ABUNDANCE,
            metadata={"notes": "test"}
        )

        json_str = original.to_json()
        restored = Sample.from_json(json_str)

        assert restored.sample_id == original.sample_id
        assert restored.age == original.age
        assert restored.cognitive_scores == original.cognitive_scores
        assert restored.data_type == original.data_type
        assert restored.metadata == original.metadata