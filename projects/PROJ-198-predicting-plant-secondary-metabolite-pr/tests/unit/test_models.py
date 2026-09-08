"""
Unit tests for Pydantic models in code/models/.
"""
import pytest
from datetime import datetime
from models.species import Species
from models.bgc import BGCType, BGCFeature
from models.metabolite import MetaboliteClass, Metabolite
from models.output import ModelOutput

class TestSpecies:
    def test_valid_species_creation(self):
        species = Species(
            species_id="12345",
            scientific_name="Solanum lycopersicum",
            common_name="Tomato",
            family="Solanaceae"
        )
        assert species.species_id == "12345"
        assert species.scientific_name == "Solanum lycopersicum"
        assert species.common_name == "Tomato"

    def test_empty_scientific_name_raises(self):
        with pytest.raises(ValueError):
            Species(species_id="123", scientific_name="")

    def test_whitespace_stripped(self):
        species = Species(
            species_id="  678  ",
            scientific_name="  Arabidopsis thaliana  "
        )
        assert species.species_id == "678"
        assert species.scientific_name == "Arabidopsis thaliana"

class TestBGCFeature:
    def test_valid_bgc_creation(self):
        bgc = BGCFeature(
            feature_id="bgc_001",
            species_id="12345",
            bgc_type=BGCType.POLYKETIDE,
            confidence_score=0.95
        )
        assert bgc.bgc_type == BGCType.POLYKETIDE
        assert bgc.confidence_score == 0.95

    def test_confidence_score_bounds(self):
        with pytest.raises(ValueError):
            BGCFeature(
                feature_id="bgc_002",
                species_id="12345",
                confidence_score=1.5
            )

    def test_bgctype_from_string(self):
        assert BGCType.from_string("polyketide") == BGCType.POLYKETIDE
        assert BGCType.from_string("PK") == BGCType.POLYKETIDE
        assert BGCType.from_string("non-ribosomal peptide") == BGCType.NON_RIBOSOMAL_PEPTIDE
        assert BGCType.from_string("unknown_type") == BGCType.UNKNOWN

    def test_to_binary_record(self):
        bgc = BGCFeature(
            feature_id="bgc_003",
            species_id="12345",
            bgc_type=BGCType.TERPENE,
            confidence_score=0.8
        )
        record = bgc.to_binary_record()
        assert record["species_id"] == "12345"
        assert record["present"] == 1
        assert record["type"] == "terpene"

class TestMetabolite:
    def test_valid_metabolite_creation(self):
        met = Metabolite(
            metabolite_id="PMDB0001",
            common_name="Solanine",
            inchikey="ABCDEFGHIJKLMNOPQRSTUVWXYZ-1234567890-X",
            metabolite_class=MetaboliteClass.ALKALOID
        )
        assert met.metabolite_id == "PMDB0001"
        assert met.metabolite_class == MetaboliteClass.ALKALOID

    def test_inchikey_uppercase(self):
        met = Metabolite(
            metabolite_id="PMDB0002",
            common_name="Test",
            inchikey="abcdefghijklmnopqrstuvwxyz-1234567890-x"
        )
        assert met.inchikey == met.inchikey.upper()

    def test_metaboliteclass_from_string(self):
        assert MetaboliteClass.from_string("alkaloid") == MetaboliteClass.ALKALOID
        assert MetaboliteClass.from_string("terpenoid") == MetaboliteClass.TERPENOID
        assert MetaboliteClass.from_string("flavonoid") == MetaboliteClass.FLAVONOID
        assert MetaboliteClass.from_string("unknown_class") == MetaboliteClass.UNKNOWN

    def test_harmonize_log_transform(self):
        import math
        met = Metabolite(
            metabolite_id="PMDB0003",
            common_name="Test",
            inchikey="ABCDEFGHIJKLMNOPQRSTUVWXYZ-1234567890-X",
            abundance=100.0
        )
        harmonized = met.harmonize()
        expected = math.log1p(100.0)
        assert harmonized.abundance == pytest.approx(expected)

class TestModelOutput:
    def test_valid_model_output(self):
        output = ModelOutput(
            output_id="model_run_001",
            model_type="PGLS",
            performance_metrics={"r2": 0.75, "rmse": 0.12},
            training_species_count=20
        )
        assert output.model_type == "PGLS"
        assert output.performance_metrics["r2"] == 0.75
        assert output.training_species_count == 20

    def test_timestamp_default(self):
        output = ModelOutput(
            output_id="model_run_002",
            model_type="RF",
            training_species_count=10
        )
        assert isinstance(output.timestamp, datetime)

    def test_to_summary_dict(self):
        output = ModelOutput(
            output_id="model_run_003",
            model_type="ElasticNet",
            performance_metrics={"r2": 0.65},
            training_species_count=15,
            phylogenetic_adjustment=True
        )
        summary = output.to_summary_dict()
        assert summary["model_type"] == "ElasticNet"
        assert summary["species_count"] == 15
        assert summary["phylogenetic"] is True