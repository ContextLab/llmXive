"""
Unit tests for Pydantic model definitions in code/models/.
"""
import pytest
from datetime import datetime
from code.models.species import Species
from code.models.bgc import BGCType, BGCFeature
from code.models.metabolite import MetaboliteClass, Metabolite
from code.models.output import ModelOutput


class TestSpecies:
    def test_species_creation_valid(self):
        """Test creation of a valid Species instance."""
        s = Species(
            species_id="12345",
            scientific_name="Arabidopsis thaliana",
            common_name="Thale Cress",
            family="Brassicaceae",
            genome_size_bp=135000000.0,
            assembly_accession="GCA_000001735.1"
        )
        assert s.species_id == "12345"
        assert s.scientific_name == "Arabidopsis thaliana"
        assert s.family == "Brassicaceae"

    def test_species_missing_required(self):
        """Test that missing required fields raises validation error."""
        with pytest.raises(Exception):
            Species(scientific_name="Test")  # Missing species_id

    def test_species_optional_fields(self):
        """Test handling of optional fields."""
        s = Species(
            species_id="999",
            scientific_name="Test Plant"
        )
        assert s.common_name is None
        assert s.metadata == {}


class TestBGCFeature:
    def test_bgc_feature_creation(self):
        """Test creation of a valid BGCFeature instance."""
        bgc = BGCFeature(
            feature_id="bgc_001",
            species_id="12345",
            bgc_type=BGCType.NRPS,
            confidence_score=0.95,
            start_position=1000,
            end_position=5000,
            gene_count=12
        )
        assert bgc.bgc_type == BGCType.NRPS
        assert bgc.confidence_score == 0.95
        assert bgc.start_position == 1000

    def test_bgc_confidence_bounds(self):
        """Test that confidence score must be between 0 and 1."""
        with pytest.raises(Exception):
            BGCFeature(
                feature_id="bad",
                species_id="1",
                bgc_type=BGCType.TERPENE,
                confidence_score=1.5,  # Invalid
                start_position=0,
                end_position=100
            )

    def test_bgc_unknown_type(self):
        """Test UNKNOWN BGC type."""
        bgc = BGCFeature(
            feature_id="bgc_unk",
            species_id="1",
            bgc_type=BGCType.UNKNOWN,
            confidence_score=0.1,
            start_position=0,
            end_position=100
        )
        assert bgc.bgc_type == BGCType.UNKNOWN


class TestMetabolite:
    def test_metabolite_valid(self):
        """Test creation of a valid Metabolite instance."""
        m = Metabolite(
            metabolite_id="PMDB12345",
            inchi_key="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",  # Valid format example
            common_name="Test Compound",
            chemical_class=MetaboliteClass.FLAVONOID,
            species_id="12345",
            abundance=150.5,
            abundance_unit="ng/g"
        )
        assert m.inchi_key == "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        assert m.abundance == 150.5

    def test_metabolite_inchi_key_validation(self):
        """Test InChIKey format validation."""
        # Valid key
        valid_key = "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
        m = Metabolite(
            metabolite_id="PMDB1",
            inchi_key=valid_key,
            species_id="1",
            abundance=10.0
        )
        assert m.inchi_key == valid_key

        # Invalid key (wrong length)
        with pytest.raises(Exception):
            Metabolite(
                metabolite_id="PMDB2",
                inchi_key="INVALID",
                species_id="1",
                abundance=10.0
            )

    def test_metabolite_negative_abundance(self):
        """Test that negative abundance is rejected."""
        with pytest.raises(Exception):
            Metabolite(
                metabolite_id="PMDB3",
                inchi_key="BSYNRYMUTXBXSQ-UHFFFAOYSA-N",
                species_id="1",
                abundance=-5.0
            )


class TestModelOutput:
    def test_model_output_creation(self):
        """Test creation of a valid ModelOutput instance."""
        output = ModelOutput(
            run_id="run_001",
            model_type="RandomForest",
            r_squared=0.85,
            n_samples=50,
            n_features=10,
            feature_importance={"feature_A": 0.5, "feature_B": 0.3}
        )
        assert output.run_id == "run_001"
        assert output.r_squared == 0.85
        assert output.feature_importance["feature_A"] == 0.5

    def test_model_output_timestamp(self):
        """Test that timestamp is auto-generated."""
        output = ModelOutput(
            run_id="run_002",
            model_type="PGLS",
            n_samples=20,
            n_features=5
        )
        assert isinstance(output.timestamp, datetime)

    def test_model_output_hyperparameters(self):
        """Test hyperparameters dict."""
        output = ModelOutput(
            run_id="run_003",
            model_type="ElasticNet",
            n_samples=100,
            n_features=20,
            hyperparameters={"alpha": 0.1, "l1_ratio": 0.5}
        )
        assert output.hyperparameters["alpha"] == 0.1