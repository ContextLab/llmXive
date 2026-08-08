"""
Unit tests for Pydantic models defined in code/models/.
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from models.species import Species
from models.bgc import BGCType, BGCFeature
from models.metabolite import MetaboliteClass, Metabolite
from models.output import ModelOutput


class TestSpecies:
    """Tests for the Species model."""

    def test_valid_species(self):
        """Test creation of a valid Species instance."""
        species = Species(
            species_id="sp_001",
            scientific_name="Arabidopsis thaliana",
            common_name="Mouse-ear cress",
            family="Brassicaceae",
            genome_assembly_id="NC_003070.9",
            genome_size_mb=135.0,
            chromosome_count=5,
            ploidy_level=2
        )
        assert species.species_id == "sp_001"
        assert species.scientific_name == "Arabidopsis thaliana"
        assert species.genome_size_mb == 135.0
        assert species.chromosome_count == 5

    def test_species_minimum_required_fields(self):
        """Test that only required fields are needed."""
        species = Species(
            species_id="sp_002",
            scientific_name="Oryza sativa"
        )
        assert species.species_id == "sp_002"
        assert species.common_name is None
        assert species.metadata == {}

    def test_species_invalid_genome_size(self):
        """Test validation error for negative genome size."""
        with pytest.raises(ValidationError):
            Species(
                species_id="sp_003",
                scientific_name="Zea mays",
                genome_size_mb=-100.0
            )

    def test_species_to_dict(self):
        """Test conversion to dictionary."""
        species = Species(
            species_id="sp_004",
            scientific_name="Solanum lycopersicum"
        )
        d = species.to_dict()
        assert d["species_id"] == "sp_004"
        assert d["scientific_name"] == "Solanum lycopersicum"


class TestBGCFeature:
    """Tests for the BGCFeature model."""

    def test_valid_bgc_feature(self):
        """Test creation of a valid BGCFeature instance."""
        bgc = BGCFeature(
            species_id="sp_001",
            bgc_id="bgc_001",
            bgc_type=BGCType.POLYKETIDE,
            confidence_score=0.95,
            start_position=1000,
            end_position=5000
        )
        assert bgc.bgc_type == BGCType.POLYKETIDE
        assert bgc.length == 4000
        assert bgc.confidence_score == 0.95

    def test_bgc_feature_length_calculation(self):
        """Test that length is calculated correctly."""
        bgc = BGCFeature(
            species_id="sp_001",
            bgc_id="bgc_002",
            bgc_type=BGCType.TERPENE,
            confidence_score=0.8,
            start_position=100,
            end_position=100
        )
        assert bgc.length == 0

    def test_bgc_feature_invalid_confidence(self):
        """Test validation error for confidence > 1.0."""
        with pytest.raises(ValidationError):
            BGCFeature(
                species_id="sp_001",
                bgc_id="bgc_003",
                bgc_type=BGCType.ALKALOID,
                confidence_score=1.5,
                start_position=0,
                end_position=1000
            )

    def test_bgc_feature_invalid_position(self):
        """Test validation error for negative position."""
        with pytest.raises(ValidationError):
            BGCFeature(
                species_id="sp_001",
                bgc_id="bgc_004",
                bgc_type=BGCType.UNKNOWN,
                confidence_score=0.5,
                start_position=-100,
                end_position=1000
            )


class TestMetabolite:
    """Tests for the Metabolite model."""

    def test_valid_metabolite(self):
        """Test creation of a valid Metabolite instance."""
        metab = Metabolite(
            species_id="sp_001",
            metabolite_id="PMDB000001",
            inchi_key="UHFFFAOYSA-N",
            name="Test Compound",
            metabolite_class=MetaboliteClass.TERPENE,
            abundance=125.5
        )
        assert metab.inchi_key == "UHFFFAOYSA-N"
        assert metab.abundance == 125.5

    def test_metabolite_invalid_inchi_key(self):
        """Test validation error for invalid InChIKey format."""
        with pytest.raises(ValidationError):
            Metabolite(
                species_id="sp_001",
                metabolite_id="PMDB000002",
                inchi_key="INVALID",
                metabolite_class=MetaboliteClass.ALKALOID,
                abundance=50.0
            )

    def test_metabolite_negative_abundance(self):
        """Test validation error for negative abundance."""
        with pytest.raises(ValidationError):
            Metabolite(
                species_id="sp_001",
                metabolite_id="PMDB000003",
                inchi_key="UHFFFAOYSA-N",
                metabolite_class=MetaboliteClass.POLYKETIDE,
                abundance=-10.0
            )

    def test_metabolite_to_json(self):
        """Test conversion to JSON."""
        metab = Metabolite(
            species_id="sp_001",
            metabolite_id="PMDB000004",
            inchi_key="JYJIGFIDKWBXDU-UHFFFAOYSA-N",
            metabolite_class=MetaboliteClass.NON_RIBOSOMAL_PEPTIDE,
            abundance=100.0
        )
        json_str = metab.to_json()
        assert "PMDB000004" in json_str
        assert "non-ribosomal peptide" in json_str


class TestModelOutput:
    """Tests for the ModelOutput model."""

    def test_valid_model_output(self):
        """Test creation of a valid ModelOutput instance."""
        output = ModelOutput(
            model_id="model_001",
            model_type="PGLS",
            species_id="sp_001",
            predicted_metabolite_class="terpene",
            predicted_abundance=50.0,
            prediction_confidence=0.85,
            features_used=["polyketide", "terpene"],
            feature_importance={"polyketide": 0.6, "terpene": 0.4},
            model_metrics={"R2": 0.75}
        )
        assert output.model_id == "model_001"
        assert output.model_type == "PGLS"
        assert output.timestamp is not None

    def test_model_output_minimal(self):
        """Test creation with minimal required fields."""
        output = ModelOutput(
            model_id="model_002",
            model_type="Random Forest"
        )
        assert output.features_used == []
        assert output.feature_importance == {}
        assert output.model_metrics == {}
        assert isinstance(output.timestamp, datetime)