"""
Unit tests for Pydantic models defined in code/models/.
"""
import pytest
from datetime import datetime
from code.models.species import Species
from code.models.bgc import BGCType, BGCFeature
from code.models.metabolite import MetaboliteClass, Metabolite
from code.models.output import ModelOutput

def test_species_creation():
    """Test basic Species model creation."""
    species = Species(
        species_id="tax_12345",
        scientific_name="Arabidopsis thaliana",
        common_name="Mouse-ear cress",
        family="Brassicaceae",
        assembly_accession="GCA_000001735.1",
        genome_size_bp=135000000,
    )
    assert species.species_id == "tax_12345"
    assert species.scientific_name == "Arabidopsis thaliana"
    assert species.family == "Brassicaceae"
    assert species.genome_size_bp == 135000000

def test_species_validation_error():
    """Test that missing required fields raise validation errors."""
    with pytest.raises(Exception):
        Species(scientific_name="Incomplete")

def test_bgc_feature_creation():
    """Test BGCFeature model creation."""
    bgc = BGCFeature(
        feature_id="bgc_001",
        species_id="tax_12345",
        bgc_type=BGCType.POLYKETIDE,
        confidence_score=0.95,
        start_position=1000,
        end_position=5000,
        gene_count=12,
    )
    assert bgc.bgc_type == BGCType.POLYKETIDE
    assert bgc.confidence_score == 0.95
    assert bgc.start_position == 1000

def test_bgc_type_enum():
    """Test BGCType enum values."""
    assert BGCType.POLYKETIDE.value == "polyketide"
    assert BGCType.UNKNOWN.value == "unknown"

def test_metabolite_inchi_key_validation():
    """Test InChIKey validation in Metabolite model."""
    # Valid InChIKey
    valid_key = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
    metabolite = Metabolite(
        metabolite_id="PMDB000001",
        inchi_key=valid_key,
        chemical_name="Test Compound",
        metabolite_class=MetaboliteClass.ALKALOIDS,
        species_id="tax_12345",
        abundance_value=10.5,
    )
    assert metabolite.inchi_key == valid_key

    # Invalid InChIKey (too short)
    with pytest.raises(Exception):
        Metabolite(
            metabolite_id="PMDB000002",
            inchi_key="INVALID",
            chemical_name="Bad Compound",
            metabolite_class=MetaboliteClass.ALKALOIDS,
            species_id="tax_12345",
            abundance_value=10.5,
        )

def test_metabolite_class_enum():
    """Test MetaboliteClass enum values."""
    assert MetaboliteClass.TERPENOIDS.value == "terpenoids"
    assert MetaboliteClass.UNKNOWN.value == "unknown"

def test_model_output_creation():
    """Test ModelOutput model creation."""
    output = ModelOutput(
        run_id="run_001",
        model_type="PGLS",
        species_ids=["tax_12345", "tax_67890"],
        target_metabolite="alkaloids",
        performance_metrics={"r2": 0.75, "rmse": 0.12},
        phylogenetic_correction_applied=True,
    )
    assert output.run_id == "run_001"
    assert output.model_type == "PGLS"
    assert output.performance_metrics["r2"] == 0.75
    assert output.phylogenetic_correction_applied is True
    assert isinstance(output.created_at, datetime)