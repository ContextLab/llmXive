"""
Unit tests for code/utils/data_models.py
"""
import pytest
from code.utils.data_models import DataType, Taxon, Sample
from datetime import datetime


class TestDataTypeEnum:
    def test_datatype_values(self):
        assert DataType.GUT_MICROBIOME.value == "gut_microbiome"
        assert DataType.COGNITIVE_SCORE.value == "cognitive_score"
        assert DataType.COVARIATE.value == "covariate"

    def test_datatype_from_string(self):
        assert DataType("gut_microbiome") == DataType.GUT_MICROBIOME
        assert DataType("cognitive_score") == DataType.COGNITIVE_SCORE


class TestTaxon:
    def test_taxon_creation(self):
        taxon = Taxon(
            taxon_id="GUT_001",
            name="Bacteroides",
            rank="genus",
            abundance=0.25,
            data_type=DataType.GUT_MICROBIOME
        )
        assert taxon.taxon_id == "GUT_001"
        assert taxon.name == "Bacteroides"
        assert taxon.rank == "genus"
        assert taxon.abundance == 0.25
        assert taxon.data_type == DataType.GUT_MICROBIOME

    def test_taxon_to_dict(self):
        taxon = Taxon(
            taxon_id="GUT_002",
            name="Firmicutes",
            rank="phylum",
            abundance=0.75,
            data_type=DataType.GUT_MICROBIOME
        )
        result = taxon.to_dict()
        assert result["taxon_id"] == "GUT_002"
        assert result["name"] == "Firmicutes"
        assert result["rank"] == "phylum"
        assert result["abundance"] == 0.75
        assert result["data_type"] == "gut_microbiome"

    def test_taxon_from_dict(self):
        data = {
            "taxon_id": "GUT_003",
            "name": "Proteobacteria",
            "rank": "phylum",
            "abundance": 0.10,
            "data_type": "gut_microbiome"
        }
        taxon = Taxon.from_dict(data)
        assert taxon.taxon_id == "GUT_003"
        assert taxon.name == "Proteobacteria"
        assert taxon.rank == "phylum"
        assert taxon.abundance == 0.10
        assert taxon.data_type == DataType.GUT_MICROBIOME


class TestSample:
    def test_sample_creation(self):
        sample = Sample(
            sample_id="S001",
            participant_id="P123",
            collection_date=datetime(2023, 1, 15),
            age=65,
            sex="M",
            bmi=24.5,
            cognitive_score=85.0,
            data_type=DataType.COGNITIVE_SCORE
        )
        assert sample.sample_id == "S001"
        assert sample.participant_id == "P123"
        assert sample.age == 65
        assert sample.sex == "M"
        assert sample.bmi == 24.5
        assert sample.cognitive_score == 85.0
        assert sample.data_type == DataType.COGNITIVE_SCORE

    def test_sample_to_dict(self):
        sample = Sample(
            sample_id="S002",
            participant_id="P456",
            collection_date=datetime(2023, 2, 20),
            age=70,
            sex="F",
            bmi=22.0,
            cognitive_score=90.0,
            data_type=DataType.COGNITIVE_SCORE
        )
        result = sample.to_dict()
        assert result["sample_id"] == "S002"
        assert result["participant_id"] == "P456"
        assert result["age"] == 70
        assert result["sex"] == "F"
        assert result["bmi"] == 22.0
        assert result["cognitive_score"] == 90.0
        assert result["data_type"] == "cognitive_score"

    def test_sample_from_dict(self):
        data = {
            "sample_id": "S003",
            "participant_id": "P789",
            "collection_date": "2023-03-25",
            "age": 62,
            "sex": "M",
            "bmi": 26.0,
            "cognitive_score": 78.0,
            "data_type": "cognitive_score"
        }
        sample = Sample.from_dict(data)
        assert sample.sample_id == "S003"
        assert sample.participant_id == "P789"
        assert sample.age == 62
        assert sample.sex == "M"
        assert sample.bmi == 26.0
        assert sample.cognitive_score == 78.0
        assert sample.data_type == DataType.COGNITIVE_SCORE

    def test_sample_invalid_age(self):
        with pytest.raises(ValueError):
            Sample(
                sample_id="S004",
                participant_id="P999",
                collection_date=datetime(2023, 4, 1),
                age=40,
                sex="M",
                bmi=23.0,
                cognitive_score=80.0,
                data_type=DataType.COGNITIVE_SCORE
            )
