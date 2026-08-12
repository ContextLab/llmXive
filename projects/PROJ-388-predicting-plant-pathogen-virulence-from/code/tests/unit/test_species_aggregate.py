"""
Unit tests for the SpeciesAggregate model.
"""
import pytest
from src.models.species_aggregate import SpeciesAggregate


class TestSpeciesAggregate:
    """Tests for SpeciesAggregate dataclass."""

    def test_creation_valid(self):
        """Test creating a valid SpeciesAggregate instance."""
        agg = SpeciesAggregate(
            species_name="Fusarium graminearum",
            avg_phenotype=0.85,
            isolate_count=12,
            variance=0.02
        )
        assert agg.species_name == "Fusarium graminearum"
        assert agg.avg_phenotype == 0.85
        assert agg.isolate_count == 12
        assert agg.variance == 0.02
        assert agg.metadata is None

    def test_creation_with_metadata(self):
        """Test creating an instance with metadata."""
        agg = SpeciesAggregate(
            species_name="Pseudomonas syringae",
            avg_phenotype=0.45,
            isolate_count=5,
            variance=0.01,
            metadata={"source": "PHI-base", "method": "mean"}
        )
        assert agg.metadata == {"source": "PHI-base", "method": "mean"}

    def test_to_dict(self):
        """Test serialization to dictionary."""
        agg = SpeciesAggregate(
            species_name="Xanthomonas spp.",
            avg_phenotype=0.60,
            isolate_count=8,
            variance=0.03
        )
        data = agg.to_dict()
        assert data["species_name"] == "Xanthomonas spp."
        assert data["avg_phenotype"] == 0.60
        assert data["isolate_count"] == 8
        assert data["variance"] == 0.03

    def test_to_dict_with_metadata(self):
        """Test serialization including metadata."""
        agg = SpeciesAggregate(
            species_name="Fusarium graminearum",
            avg_phenotype=0.90,
            isolate_count=10,
            variance=0.01,
            metadata={"note": "high virulence"}
        )
        data = agg.to_dict()
        assert "metadata" in data
        assert data["metadata"]["note"] == "high virulence"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "species_name": "Pseudomonas syringae",
            "avg_phenotype": 0.55,
            "isolate_count": 6,
            "variance": 0.04
        }
        agg = SpeciesAggregate.from_dict(data)
        assert agg.species_name == "Pseudomonas syringae"
        assert agg.avg_phenotype == 0.55
        assert agg.isolate_count == 6
        assert agg.variance == 0.04

    def test_from_dict_with_metadata(self):
        """Test deserialization with optional metadata."""
        data = {
            "species_name": "Xanthomonas spp.",
            "avg_phenotype": 0.70,
            "isolate_count": 4,
            "variance": 0.02,
            "metadata": {"source": "literature"}
        }
        agg = SpeciesAggregate.from_dict(data)
        assert agg.metadata == {"source": "literature"}

    def test_invalid_isolate_count_zero(self):
        """Test that zero isolate_count raises ValueError."""
        with pytest.raises(ValueError):
            SpeciesAggregate(
                species_name="Test sp.",
                avg_phenotype=0.5,
                isolate_count=0,
                variance=0.0
            )

    def test_invalid_isolate_count_negative(self):
        """Test that negative isolate_count raises ValueError."""
        with pytest.raises(ValueError):
            SpeciesAggregate(
                species_name="Test sp.",
                avg_phenotype=0.5,
                isolate_count=-1,
                variance=0.0
            )

    def test_invalid_variance_negative(self):
        """Test that negative variance raises ValueError."""
        with pytest.raises(ValueError):
            SpeciesAggregate(
                species_name="Test sp.",
                avg_phenotype=0.5,
                isolate_count=1,
                variance=-0.1
            )

    def test_invalid_avg_phenotype_type(self):
        """Test that non-numeric avg_phenotype raises TypeError."""
        with pytest.raises(TypeError):
            SpeciesAggregate(
                species_name="Test sp.",
                avg_phenotype="high",
                isolate_count=1,
                variance=0.0
            )

    def test_invalid_variance_type(self):
        """Test that non-numeric variance raises TypeError."""
        with pytest.raises(TypeError):
            SpeciesAggregate(
                species_name="Test sp.",
                avg_phenotype=0.5,
                isolate_count=1,
                variance="low"
            )