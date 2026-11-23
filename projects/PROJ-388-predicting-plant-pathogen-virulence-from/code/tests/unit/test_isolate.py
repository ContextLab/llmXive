"""
Unit tests for the Isolate data model.
"""

import pytest
from src.models.isolate import Isolate


class TestIsolate:
    """Test cases for the Isolate class."""

    def test_isolate_creation(self):
        """Test basic Isolate creation with valid data."""
        isolate = Isolate(
            strain_id="FG001",
            species="Fusarium graminearum",
            genome_path="data/raw/FG001.fna",
            phenotype_score=0.85,
            metadata={"source": "NCBI", "year": 2023}
        )
        
        assert isolate.strain_id == "FG001"
        assert isolate.species == "Fusarium graminearum"
        assert isolate.genome_path == "data/raw/FG001.fna"
        assert isolate.phenotype_score == 0.85
        assert isolate.metadata == {"source": "NCBI", "year": 2023}

    def test_isolate_default_metadata(self):
        """Test that metadata defaults to empty dict when not provided."""
        isolate = Isolate(
            strain_id="PS002",
            species="Pseudomonas syringae",
            genome_path="data/raw/PS002.fna",
            phenotype_score=0.62
        )
        
        assert isolate.metadata == {}

    def test_isolate_to_dict(self):
        """Test conversion of Isolate to dictionary."""
        isolate = Isolate(
            strain_id="XO003",
            species="Xanthomonas oryzae",
            genome_path="data/raw/XO003.fna",
            phenotype_score=0.91,
            metadata={"location": "Asia"}
        )
        
        result = isolate.to_dict()
        
        assert result["strain_id"] == "XO003"
        assert result["species"] == "Xanthomonas oryzae"
        assert result["genome_path"] == "data/raw/XO003.fna"
        assert result["phenotype_score"] == 0.91
        assert result["metadata"] == {"location": "Asia"}

    def test_isolate_from_dict(self):
        """Test creation of Isolate from dictionary."""
        data = {
            "strain_id": "FG004",
            "species": "Fusarium graminearum",
            "genome_path": "data/raw/FG004.fna",
            "phenotype_score": 0.78,
            "metadata": {"source": "PHI-base"}
        }
        
        isolate = Isolate.from_dict(data)
        
        assert isolate.strain_id == "FG004"
        assert isolate.species == "Fusarium graminearum"
        assert isolate.genome_path == "data/raw/FG004.fna"
        assert isolate.phenotype_score == 0.78
        assert isolate.metadata == {"source": "PHI-base"}

    def test_isolate_from_dict_missing_metadata(self):
        """Test Isolate.from_dict handles missing metadata gracefully."""
        data = {
            "strain_id": "PS005",
            "species": "Pseudomonas syringae",
            "genome_path": "data/raw/PS005.fna",
            "phenotype_score": 0.55
        }
        
        isolate = Isolate.from_dict(data)
        
        assert isolate.metadata == {}

    def test_isolate_invalid_strain_id_empty(self):
        """Test that empty strain_id raises ValueError."""
        with pytest.raises(ValueError, match="strain_id must be a non-empty string"):
            Isolate(
                strain_id="",
                species="Test species",
                genome_path="path/to/file.fna",
                phenotype_score=0.5
            )

    def test_isolate_invalid_strain_id_type(self):
        """Test that non-string strain_id raises ValueError."""
        with pytest.raises(ValueError, match="strain_id must be a non-empty string"):
            Isolate(
                strain_id=123,
                species="Test species",
                genome_path="path/to/file.fna",
                phenotype_score=0.5
            )

    def test_isolate_invalid_species_empty(self):
        """Test that empty species raises ValueError."""
        with pytest.raises(ValueError, match="species must be a non-empty string"):
            Isolate(
                strain_id="TEST001",
                species="",
                genome_path="path/to/file.fna",
                phenotype_score=0.5
            )

    def test_isolate_invalid_genome_path_empty(self):
        """Test that empty genome_path raises ValueError."""
        with pytest.raises(ValueError, match="genome_path must be a non-empty string"):
            Isolate(
                strain_id="TEST001",
                species="Test species",
                genome_path="",
                phenotype_score=0.5
            )

    def test_isolate_invalid_phenotype_score_type(self):
        """Test that non-numeric phenotype_score raises ValueError."""
        with pytest.raises(ValueError, match="phenotype_score must be a numeric value"):
            Isolate(
                strain_id="TEST001",
                species="Test species",
                genome_path="path/to/file.fna",
                phenotype_score="high"
            )

    def test_isolate_invalid_metadata_type(self):
        """Test that non-dict metadata raises ValueError."""
        with pytest.raises(ValueError, match="metadata must be a dictionary"):
            Isolate(
                strain_id="TEST001",
                species="Test species",
                genome_path="path/to/file.fna",
                phenotype_score=0.5,
                metadata="not a dict"
            )

    def test_isolate_phenotype_score_integer(self):
        """Test that integer phenotype_score is accepted."""
        isolate = Isolate(
            strain_id="TEST001",
            species="Test species",
            genome_path="path/to/file.fna",
            phenotype_score=5
        )
        
        assert isolate.phenotype_score == 5

    def test_isolate_zero_phenotype_score(self):
        """Test that zero phenotype_score is accepted."""
        isolate = Isolate(
            strain_id="TEST001",
            species="Test species",
            genome_path="path/to/file.fna",
            phenotype_score=0.0
        )
        
        assert isolate.phenotype_score == 0.0