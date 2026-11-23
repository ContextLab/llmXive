import pytest
from src.models.isolate import Isolate


class TestIsolate:
    """Unit tests for the Isolate data class."""

    def test_isolate_creation_required_fields(self):
        """Test creation with only required fields."""
        isolate = Isolate(
            strain_id="Fg-001",
            species="Fusarium graminearum",
            genome_path="data/raw/Fg-001.fna",
            phenotype_score=0.85
        )
        assert isolate.strain_id == "Fg-001"
        assert isolate.species == "Fusarium graminearum"
        assert isolate.genome_path == "data/raw/Fg-001.fna"
        assert isolate.phenotype_score == 0.85
        assert isolate.metadata == {}

    def test_isolate_creation_with_metadata(self):
        """Test creation with custom metadata."""
        metadata = {"source": "NCBI", "assembly_level": "Complete"}
        isolate = Isolate(
            strain_id="Ps-002",
            species="Pseudomonas syringae",
            genome_path="data/raw/Ps-002.fna",
            phenotype_score=0.42,
            metadata=metadata
        )
        assert isolate.metadata == metadata
        assert isolate.metadata["source"] == "NCBI"

    def test_isolate_phenotype_score_type(self):
        """Ensure phenotype_score is a float."""
        isolate = Isolate(
            strain_id="Xo-003",
            species="Xanthomonas oryzae",
            genome_path="data/raw/Xo-003.fna",
            phenotype_score=0.0
        )
        assert isinstance(isolate.phenotype_score, float)

    def test_isolate_default_metadata(self):
        """Test that metadata defaults to an empty dict and is mutable."""
        isolate = Isolate(
            strain_id="Test-004",
            species="Test species",
            genome_path="path/to/file.fna",
            phenotype_score=0.5
        )
        isolate.metadata["new_key"] = "value"
        assert isolate.metadata["new_key"] == "value"
        # Ensure it didn't affect another instance (dataclass default_factory behavior)
        isolate2 = Isolate(
            strain_id="Test-005",
            species="Test species",
            genome_path="path/to/file2.fna",
            phenotype_score=0.5
        )
        assert "new_key" not in isolate2.metadata