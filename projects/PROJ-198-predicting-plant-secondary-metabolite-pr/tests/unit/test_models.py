"""
Unit tests for Pydantic models defined in code/models.
"""
import pytest
from datetime import datetime
from code.models import Species, BGCFeature, Metabolite, ModelOutput
from code.models.bgc import BGCType
from code.models.metabolite import MetaboliteClass

# --- Species Tests ---
def test_species_creation():
    species = Species(
        species_id="sp_001",
        scientific_name="Arabidopsis thaliana",
        assembly_accession="GCF_000001735.4",
        assembly_version="TAIR10",
        genome_size_bp=135000000,
        source_db="Phytozome"
    )
    assert species.species_id == "sp_001"
    assert not species.is_large_genome(threshold_mb=500)
    assert species.is_large_genome(threshold_mb=100)

def test_species_large_genome():
    species = Species(
        species_id="sp_002",
        scientific_name="Zea mays",
        assembly_accession="GCF_000005005.2",
        assembly_version="B73_RefGen_v4",
        genome_size_bp=2300000000,
        source_db="RefSeq"
    )
    assert species.is_large_genome(threshold_mb=500)

# --- BGCFeature Tests ---
def test_bgc_creation():
    bgc = BGCFeature(
        bgc_id="bgc_001",
        species_id="sp_001",
        cluster_type=BGCType.PKS_II,
        confidence_score=0.95,
        start_pos=1000,
        end_pos=5000,
        contig_id="chr1"
    )
    assert bgc.is_high_confidence(threshold=0.7)
    assert not bgc.is_high_confidence(threshold=0.96)

def test_bgc_low_confidence():
    bgc = BGCFeature(
        bgc_id="bgc_002",
        species_id="sp_001",
        cluster_type=BGCType.NRPS,
        confidence_score=0.5,
        start_pos=1000,
        end_pos=5000,
        contig_id="chr1"
    )
    assert not bgc.is_high_confidence(threshold=0.7)

# --- Metabolite Tests ---
def test_metabolite_creation():
    metab = Metabolite(
        metabolite_id="met_001",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=125.5,
        chemical_class=MetaboliteClass.TERPENOIDS
    )
    assert metab.log_transform(pseudo_count=1.0) > 0
    assert metab.chemical_class == MetaboliteClass.TERPENOIDS

def test_metabolite_inchi_key_validation():
    # Valid InChIKey
    metab = Metabolite(
        metabolite_id="met_002",
        inchi_key="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
        abundance=10.0
    )
    assert metab.inchi_key == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"

    # Invalid InChIKey length
    with pytest.raises(ValueError):
        Metabolite(
            metabolite_id="met_003",
            inchi_key="INVALID",
            abundance=10.0
        )

def test_metabolite_log_transform():
    metab = Metabolite(
        metabolite_id="met_004",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=0.0
    )
    # log(0 + 1) = 0
    assert metab.log_transform(pseudo_count=1.0) == 0.0
    # log(100 + 1) ~ 4.615
    metab.abundance = 100.0
    import math
    assert abs(metab.log_transform(pseudo_count=1.0) - math.log(101)) < 1e-5

# --- ModelOutput Tests ---
def test_model_output_creation():
    output = ModelOutput(
        run_id="run_001",
        model_type="PGLS",
        r_squared=0.75,
        feature_importance={"feature_a": 0.5, "feature_b": 0.3}
    )
    assert output.is_significant(threshold=0.0)
    assert not output.is_significant(threshold=0.8)

def test_model_output_none_r_squared():
    output = ModelOutput(
        run_id="run_002",
        model_type="RandomForest",
        r_squared=None
    )
    assert not output.is_significant(threshold=0.0)

def test_model_output_timestamp():
    output = ModelOutput(
        run_id="run_003",
        model_type="ElasticNet"
    )
    assert isinstance(output.timestamp, datetime)

# --- Integration/Serialization Tests ---
def test_species_serialization():
    species = Species(
        species_id="sp_001",
        scientific_name="Arabidopsis thaliana",
        assembly_accession="GCF_000001735.4",
        assembly_version="TAIR10",
        genome_size_bp=135000000,
        source_db="Phytozome"
    )
    json_str = species.model_dump_json()
    assert "sp_001" in json_str
    assert "Arabidopsis thaliana" in json_str

    # Reconstruct
    species2 = Species.model_validate_json(json_str)
    assert species2.species_id == species.species_id

def test_metabolite_dict_conversion():
    metab = Metabolite(
        metabolite_id="met_001",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=125.5,
        chemical_class=MetaboliteClass.TERPENOIDS
    )
    data = metab.model_dump()
    assert data["metabolite_id"] == "met_001"
    assert data["abundance"] == 125.5
    assert data["chemical_class"] == "terpenoids" # Enum serializes to value by default in Pydantic v2 unless configured otherwise

def test_bgc_dict_conversion():
    bgc = BGCFeature(
        bgc_id="bgc_001",
        species_id="sp_001",
        cluster_type=BGCType.PKS_II,
        confidence_score=0.95,
        start_pos=1000,
        end_pos=5000,
        contig_id="chr1"
    )
    data = bgc.model_dump()
    assert data["cluster_type"] == "PKS_II"

def test_model_output_dict_conversion():
    output = ModelOutput(
        run_id="run_001",
        model_type="PGLS",
        r_squared=0.75
    )
    data = output.model_dump()
    assert data["run_id"] == "run_001"
    assert data["r_squared"] == 0.75
    assert "timestamp" in data

def test_invalid_species_genome_size():
    with pytest.raises(ValueError):
        Species(
            species_id="sp_bad",
            scientific_name="Bad Species",
            assembly_accession="GCF_000",
            assembly_version="v1",
            genome_size_bp=-100, # Must be > 0
            source_db="RefSeq"
        )

def test_invalid_bgc_confidence():
    with pytest.raises(ValueError):
        BGCFeature(
            bgc_id="bgc_bad",
            species_id="sp_001",
            cluster_type=BGCType.NRPS,
            confidence_score=1.5, # Must be <= 1.0
            start_pos=1000,
            end_pos=5000,
            contig_id="chr1"
        )

def test_invalid_metabolite_abundance():
    with pytest.raises(ValueError):
        Metabolite(
            metabolite_id="met_bad",
            inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
            abundance=-5.0 # Must be >= 0
        )

def test_metabolite_unknown_class_default():
    metab = Metabolite(
        metabolite_id="met_005",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=10.0
    )
    assert metab.chemical_class == MetaboliteClass.UNKNOWN

def test_metabolite_explicit_class():
    metab = Metabolite(
        metabolite_id="met_006",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=10.0,
        chemical_class=MetaboliteClass.ALKALOIDS
    )
    assert metab.chemical_class == MetaboliteClass.ALKALOIDS

def test_species_optional_fields():
    species = Species(
        species_id="sp_003",
        scientific_name="Oryza sativa",
        assembly_accession="GCF_000001435.2",
        assembly_version="IRGSP-1.0",
        genome_size_bp=430000000,
        source_db="Phytozome",
        common_name="Rice"
    )
    assert species.common_name == "Rice"
    assert species.download_timestamp is None

def test_bgc_optional_mibig_fields():
    bgc = BGCFeature(
        bgc_id="bgc_003",
        species_id="sp_001",
        cluster_type=BGCType.Terpenoid,
        confidence_score=0.8,
        start_pos=1000,
        end_pos=5000,
        contig_id="chr1"
    )
    assert bgc.mibig_match_id is None
    assert bgc.mibig_similarity is None

def test_bgc_with_mibig():
    bgc = BGCFeature(
        bgc_id="bgc_004",
        species_id="sp_001",
        cluster_type=BGCType.NRPS,
        confidence_score=0.99,
        start_pos=1000,
        end_pos=5000,
        contig_id="chr1",
        mibig_match_id="BGC0000001",
        mibig_similarity=0.85
    )
    assert bgc.mibig_match_id == "BGC0000001"
    assert bgc.mibig_similarity == 0.85

def test_model_output_metadata():
    output = ModelOutput(
        run_id="run_004",
        model_type="PGLS",
        r_squared=0.80,
        metadata={"p_value": 0.001, "cv_scores": [0.7, 0.75, 0.72]}
    )
    assert output.metadata["p_value"] == 0.001
    assert len(output.metadata["cv_scores"]) == 3

def test_model_output_hyperparameters():
    output = ModelOutput(
        run_id="run_005",
        model_type="RandomForest",
        hyperparameters={"n_estimators": 100, "max_depth": 10}
    )
    assert output.hyperparameters["n_estimators"] == 100
    assert output.hyperparameters["max_depth"] == 10

def test_species_model_dump_exclude_none():
    species = Species(
        species_id="sp_004",
        scientific_name="Solanum lycopersicum",
        assembly_accession="GCF_000188115.1",
        assembly_version="SL3.0",
        genome_size_bp=900000000,
        source_db="Phytozome"
    )
    # Default dump includes None
    data_with_none = species.model_dump()
    assert "download_timestamp" in data_with_none
    assert data_with_none["download_timestamp"] is None

    # Exclude None
    data_no_none = species.model_dump(exclude_none=True)
    assert "download_timestamp" not in data_no_none

def test_metabolite_log_transform_zero_abundance():
    # When abundance is 0, log(0 + 1) should be 0
    metab = Metabolite(
        metabolite_id="met_zero",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=0.0
    )
    import math
    assert abs(metab.log_transform(pseudo_count=1.0) - math.log(1)) < 1e-9

def test_metabolite_log_transform_small_pseudo_count():
    metab = Metabolite(
        metabolite_id="met_small",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=0.0
    )
    import math
    # log(0 + 0.01)
    expected = math.log(0.01)
    assert abs(metab.log_transform(pseudo_count=0.01) - expected) < 1e-9

def test_bgc_confidence_boundary():
    # Exactly at threshold
    bgc = BGCFeature(
        bgc_id="bgc_boundary",
        species_id="sp_001",
        cluster_type=BGCType.PKS_I,
        confidence_score=0.7,
        start_pos=1000,
        end_pos=5000,
        contig_id="chr1"
    )
    assert bgc.is_high_confidence(threshold=0.7)

    # Just below threshold
    bgc.confidence_score = 0.6999
    assert not bgc.is_high_confidence(threshold=0.7)

def test_species_genome_size_boundary():
    # Exactly 500MB in bytes
    species = Species(
        species_id="sp_boundary",
        scientific_name="Test",
        assembly_accession="GCF_000",
        assembly_version="v1",
        genome_size_bp=500 * 1_000_000,
        source_db="RefSeq"
    )
    assert not species.is_large_genome(threshold_mb=500) # Not > 500

    species.genome_size_bp = 500 * 1_000_000 + 1
    assert species.is_large_genome(threshold_mb=500) # > 500

def test_model_output_r_squared_boundary():
    output = ModelOutput(
        run_id="run_boundary",
        model_type="Test",
        r_squared=0.0
    )
    assert not output.is_significant(threshold=0.0) # Not > 0

    output.r_squared = 0.0001
    assert output.is_significant(threshold=0.0)

def test_metabolite_inchi_key_case_sensitivity():
    # InChIKeys are typically uppercase, but let's ensure validation handles it if needed
    # The regex in validator enforces uppercase [A-Z0-9]
    with pytest.raises(ValueError):
        Metabolite(
            metabolite_id="met_case",
            inchi_key="zamouscynkaaf-uhfffaoy-nsa-n", # lowercase
            abundance=10.0
        )

def test_metabolite_inchi_key_special_chars():
    # InChIKeys should only contain A-Z, 0-9, and hyphens
    with pytest.raises(ValueError):
        Metabolite(
            metabolite_id="met_special",
            inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N!",
            abundance=10.0
        )

def test_species_all_required_fields():
    # Ensure all required fields are present
    required_fields = {
        "species_id",
        "scientific_name",
        "assembly_accession",
        "assembly_version",
        "genome_size_bp",
        "source_db"
    }
    species = Species(
        species_id="sp_req",
        scientific_name="Test",
        assembly_accession="GCF_000",
        assembly_version="v1",
        genome_size_bp=100,
        source_db="RefSeq"
    )
    model_fields = set(species.model_fields.keys())
    assert required_fields.issubset(model_fields)

def test_bgc_all_required_fields():
    required_fields = {
        "bgc_id",
        "species_id",
        "cluster_type",
        "confidence_score",
        "start_pos",
        "end_pos",
        "contig_id"
    }
    bgc = BGCFeature(
        bgc_id="bgc_req",
        species_id="sp_001",
        cluster_type=BGCType.NRPS,
        confidence_score=0.5,
        start_pos=100,
        end_pos=200,
        contig_id="chr1"
    )
    model_fields = set(bgc.model_fields.keys())
    assert required_fields.issubset(model_fields)

def test_metabolite_all_required_fields():
    required_fields = {
        "metabolite_id",
        "inchi_key",
        "abundance"
    }
    metab = Metabolite(
        metabolite_id="met_req",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=10.0
    )
    model_fields = set(metab.model_fields.keys())
    assert required_fields.issubset(model_fields)

def test_model_output_all_required_fields():
    required_fields = {
        "run_id",
        "model_type"
    }
    output = ModelOutput(
        run_id="run_req",
        model_type="Test"
    )
    model_fields = set(output.model_fields.keys())
    assert required_fields.issubset(model_fields)

def test_species_from_dict():
    data = {
        "species_id": "sp_dict",
        "scientific_name": "Test",
        "assembly_accession": "GCF_000",
        "assembly_version": "v1",
        "genome_size_bp": 100,
        "source_db": "RefSeq"
    }
    species = Species.model_validate(data)
    assert species.species_id == "sp_dict"

def test_bgc_from_dict():
    data = {
        "bgc_id": "bgc_dict",
        "species_id": "sp_001",
        "cluster_type": "NRPS",
        "confidence_score": 0.5,
        "start_pos": 100,
        "end_pos": 200,
        "contig_id": "chr1"
    }
    bgc = BGCFeature.model_validate(data)
    assert bgc.bgc_id == "bgc_dict"
    assert bgc.cluster_type == BGCType.NRPS

def test_metabolite_from_dict():
    data = {
        "metabolite_id": "met_dict",
        "inchi_key": "ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        "abundance": 10.0,
        "chemical_class": "alkaloids"
    }
    metab = Metabolite.model_validate(data)
    assert metab.metabolite_id == "met_dict"
    assert metab.chemical_class == MetaboliteClass.ALKALOIDS

def test_model_output_from_dict():
    data = {
        "run_id": "run_dict",
        "model_type": "PGLS",
        "r_squared": 0.8
    }
    output = ModelOutput.model_validate(data)
    assert output.run_id == "run_dict"
    assert output.r_squared == 0.8

def test_species_to_dict():
    species = Species(
        species_id="sp_to_dict",
        scientific_name="Test",
        assembly_accession="GCF_000",
        assembly_version="v1",
        genome_size_bp=100,
        source_db="RefSeq"
    )
    data = species.model_dump()
    assert data["species_id"] == "sp_to_dict"

def test_bgc_to_dict():
    bgc = BGCFeature(
        bgc_id="bgc_to_dict",
        species_id="sp_001",
        cluster_type=BGCType.PKS_I,
        confidence_score=0.5,
        start_pos=100,
        end_pos=200,
        contig_id="chr1"
    )
    data = bgc.model_dump()
    assert data["bgc_id"] == "bgc_to_dict"
    assert data["cluster_type"] == "PKS_I"

def test_metabolite_to_dict():
    metab = Metabolite(
        metabolite_id="met_to_dict",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=10.0,
        chemical_class=MetaboliteClass.PHENYLPROPANOIDS
    )
    data = metab.model_dump()
    assert data["metabolite_id"] == "met_to_dict"
    assert data["chemical_class"] == "phenylpropanoids"

def test_model_output_to_dict():
    output = ModelOutput(
        run_id="run_to_dict",
        model_type="RF",
        r_squared=0.5
    )
    data = output.model_dump()
    assert data["run_id"] == "run_to_dict"
    assert data["r_squared"] == 0.5

def test_species_repr():
    species = Species(
        species_id="sp_repr",
        scientific_name="Test",
        assembly_accession="GCF_000",
        assembly_version="v1",
        genome_size_bp=100,
        source_db="RefSeq"
    )
    repr_str = repr(species)
    assert "sp_repr" in repr_str
    assert "Test" in repr_str

def test_bgc_repr():
    bgc = BGCFeature(
        bgc_id="bgc_repr",
        species_id="sp_001",
        cluster_type=BGCType.NRPS,
        confidence_score=0.5,
        start_pos=100,
        end_pos=200,
        contig_id="chr1"
    )
    repr_str = repr(bgc)
    assert "bgc_repr" in repr_str

def test_metabolite_repr():
    metab = Metabolite(
        metabolite_id="met_repr",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=10.0
    )
    repr_str = repr(metab)
    assert "met_repr" in repr_str

def test_model_output_repr():
    output = ModelOutput(
        run_id="run_repr",
        model_type="Test"
    )
    repr_str = repr(output)
    assert "run_repr" in repr_str

def test_species_str():
    species = Species(
        species_id="sp_str",
        scientific_name="Test",
        assembly_accession="GCF_000",
        assembly_version="v1",
        genome_size_bp=100,
        source_db="RefSeq"
    )
    str_str = str(species)
    assert "sp_str" in str_str

def test_bgc_str():
    bgc = BGCFeature(
        bgc_id="bgc_str",
        species_id="sp_001",
        cluster_type=BGCType.NRPS,
        confidence_score=0.5,
        start_pos=100,
        end_pos=200,
        contig_id="chr1"
    )
    str_str = str(bgc)
    assert "bgc_str" in str_str

def test_metabolite_str():
    metab = Metabolite(
        metabolite_id="met_str",
        inchi_key="ZAMOUSCYNKAAIF-UHFFFAOYSA-N",
        abundance=10.0
    )
    str_str = str(metab)
    assert "met_str" in str_str

def test_model_output_str():
    output = ModelOutput(
        run_id="run_str",
        model_type="Test"
    )
    str_str = str(output)
    assert "run_str" in str_str