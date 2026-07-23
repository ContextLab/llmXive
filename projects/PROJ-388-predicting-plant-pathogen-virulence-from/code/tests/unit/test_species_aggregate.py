import pytest
from src.models.species_aggregate import SpeciesAggregate


class TestSpeciesAggregate:
    def test_initialization(self):
        """Test that SpeciesAggregate initializes with correct fields."""
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

    def test_to_dict(self):
        """Test conversion to dictionary."""
        agg = SpeciesAggregate(
            species_name="Pseudomonas syringae",
            avg_phenotype=0.45,
            isolate_count=5,
            variance=0.01
        )
        data = agg.to_dict()
        assert data == {
            "species_name": "Pseudomonas syringae",
            "avg_phenotype": 0.45,
            "isolate_count": 5,
            "variance": 0.01
        }

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "species_name": "Xanthomonas campestris",
            "avg_phenotype": 0.60,
            "isolate_count": 8,
            "variance": 0.03
        }
        agg = SpeciesAggregate.from_dict(data)
        assert agg.species_name == "Xanthomonas campestris"
        assert agg.avg_phenotype == 0.60
        assert agg.isolate_count == 8
        assert agg.variance == 0.03

    def test_round_trip(self):
        """Test that to_dict and from_dict are inverse operations."""
        original = SpeciesAggregate(
            species_name="Test Species",
            avg_phenotype=0.99,
            isolate_count=100,
            variance=0.05
        )
        reconstructed = SpeciesAggregate.from_dict(original.to_dict())
        assert original == reconstructed