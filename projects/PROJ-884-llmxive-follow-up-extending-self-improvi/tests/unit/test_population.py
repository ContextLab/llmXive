"""
Unit tests for the Population management module.
"""

import pytest
import random
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.bes.population import Population, Individual, PopulationStats, SelectionMethod, PopulationError


@pytest.fixture
def sample_fitness_function():
    """A simple fitness function that sums the genotype list."""
    def fitness(ind: Individual) -> float:
        if isinstance(ind.genotype, list):
            return sum(ind.genotype)
        return 0.0
    return fitness

@pytest.fixture
def empty_population():
    """Create an empty population."""
    return Population(max_size=10, elite_count=2)

@pytest.fixture
def small_population(sample_fitness_function):
    """Create a small initialized population."""
    pop = Population(max_size=10, elite_count=2, min_size=2)
    pop.initialize(fitness_function=sample_fitness_function, seed=42)
    return pop

class TestIndividual:
    """Tests for the Individual class."""

    def test_individual_creation(self):
        """Test basic individual creation."""
        ind = Individual(
            id="test_1",
            genotype=[1, 2, 3],
            phenotype=[1, 2, 3],
            fitness=10.0
        )
        assert ind.id == "test_1"
        assert ind.genotype == [1, 2, 3]
        assert ind.fitness == 10.0
        assert ind.age == 0

    def test_individual_to_dict(self):
        """Test serialization to dictionary."""
        ind = Individual(
            id="test_1",
            genotype=[1, 2, 3],
            phenotype=[1, 2, 3],
            fitness=10.0,
            age=5,
            parent_ids=["p1", "p2"]
        )
        data = ind.to_dict()
        assert data["id"] == "test_1"
        assert data["fitness"] == 10.0
        assert data["age"] == 5
        assert data["parent_ids"] == ["p1", "p2"]

    def test_individual_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test_2",
            "genotype": [4, 5, 6],
            "phenotype": [4, 5, 6],
            "fitness": 20.0,
            "age": 3,
            "parent_ids": ["p3"],
            "metadata": {"key": "value"}
        }
        ind = Individual.from_dict(data)
        assert ind.id == "test_2"
        assert ind.genotype == [4, 5, 6]
        assert ind.fitness == 20.0
        assert ind.metadata["key"] == "value"

class TestPopulationInitialization:
    """Tests for population initialization."""

    def test_init_parameters(self):
        """Test population initialization with various parameters."""
        pop = Population(
            max_size=50,
            elite_count=5,
            selection_method=SelectionMethod.RANK,
            tournament_size=4,
            mutation_rate=0.2,
            crossover_rate=0.8
        )
        assert pop.max_size == 50
        assert pop.elite_count == 5
        assert pop.selection_method == SelectionMethod.RANK
        assert pop.tournament_size == 4
        assert pop.mutation_rate == 0.2
        assert pop.crossover_rate == 0.8

    def test_init_validates_elite_count(self):
        """Test that elite_count > max_size raises an error."""
        with pytest.raises(PopulationError):
            Population(max_size=5, elite_count=10)

    def test_initialize_creates_individuals(self, small_population):
        """Test that initialization creates the correct number of individuals."""
        assert len(small_population._individuals) == small_population.max_size

    def test_initialize_with_custom_genotypes(self):
        """Test initialization with provided genotypes."""
        pop = Population(max_size=3)
        genotypes = [[1], [2], [3], [4]]  # More than max_size
        pop.initialize(initial_genotypes=genotypes)
        assert len(pop._individuals) == 3
        # Check that only the first 3 were used
        genos = [ind.genotype for ind in pop._individuals.values()]
        assert [1] in genos
        assert [2] in genos
        assert [3] in genos
        assert [4] not in genos

    def test_initialize_with_fitness_function(self, sample_fitness_function):
        """Test that fitness function is applied during initialization."""
        pop = Population(max_size=5)
        pop.initialize(fitness_function=sample_fitness_function, seed=123)
        for ind in pop._individuals.values():
            assert ind.fitness >= 0  # Sum of non-negative integers

class TestSelection:
    """Tests for selection mechanisms."""

    def test_select_parent_empty_population(self, empty_population):
        """Test that selecting from empty population raises error."""
        with pytest.raises(PopulationError):
            empty_population.select_parent()

    def test_select_parent_tournament(self, small_population):
        """Test tournament selection."""
        parent = small_population.select_parent()
        assert isinstance(parent, Individual)
        assert parent.id in small_population._individuals

    def test_select_parent_rank(self, small_population):
        """Test rank selection."""
        small_population.selection_method = SelectionMethod.RANK
        parent = small_population.select_parent()
        assert isinstance(parent, Individual)

    def test_select_parent_elite(self, small_population):
        """Test elite selection returns the best individual."""
        small_population.selection_method = SelectionMethod.ELITE
        parent = small_population.select_parent()
        best = max(small_population._individuals.values(), key=lambda x: x.fitness)
        assert parent.id == best.id

    def test_select_parents(self, small_population):
        """Test selecting multiple parents."""
        parents = small_population.select_parents(5)
        assert len(parents) == 5
        assert all(isinstance(p, Individual) for p in parents)

class TestCrossoverAndMutation:
    """Tests for genetic operators."""

    def test_crossover_same_length(self, small_population):
        """Test crossover with same-length genotypes."""
        p1 = Individual(id="p1", genotype=[1, 2, 3, 4], phenotype=[1, 2, 3, 4], fitness=10)
        p2 = Individual(id="p2", genotype=[5, 6, 7, 8], phenotype=[5, 6, 7, 8], fitness=20)
        
        c1, c2 = small_population.crossover(p1, p2)
        
        assert isinstance(c1, list)
        assert isinstance(c2, list)
        assert len(c1) == 4
        assert len(c2) == 4
        # Check that parts come from parents
        assert c1[:2] == p1.genotype[:2] or c1[:2] == p2.genotype[:2]

    def test_crossover_different_length(self, small_population):
        """Test crossover with different-length genotypes."""
        p1 = Individual(id="p1", genotype=[1, 2], phenotype=[1, 2], fitness=10)
        p2 = Individual(id="p2", genotype=[5, 6, 7, 8, 9], phenotype=[5, 6, 7, 8, 9], fitness=20)
        
        c1, c2 = small_population.crossover(p1, p2)
        
        assert len(c1) == 5  # Length of longer parent
        assert len(c2) == 5

    def test_crossover_no_crossover(self, small_population):
        """Test that crossover might not happen based on rate."""
        p1 = Individual(id="p1", genotype=[1, 2], phenotype=[1, 2], fitness=10)
        p2 = Individual(id="p2", genotype=[5, 6], phenotype=[5, 6], fitness=20)
        
        small_population.crossover_rate = 0.0
        c1, c2 = small_population.crossover(p1, p2)
        
        assert c1 == p1.genotype
        assert c2 == p2.genotype

    def test_mutation(self, small_population):
        """Test mutation changes genotype."""
        genotype = [1, 2, 3, 4, 5]
        mutated = small_population.mutate(genotype)
        
        assert isinstance(mutated, list)
        assert len(mutated) == len(genotype)
        # Mutation rate is 0.1, so it might not change, but structure is preserved

    def test_mutation_non_list(self, small_population):
        """Test mutation on non-list genotype returns as-is."""
        genotype = "string_genotype"
        mutated = small_population.mutate(genotype)
        assert mutated == genotype

class TestEvolution:
    """Tests for evolutionary steps."""

    def test_create_offspring(self, small_population):
        """Test offspring creation."""
        p1 = small_population.select_parent()
        p2 = small_population.select_parent()
        
        child = small_population.create_offspring(p1, p2)
        
        assert isinstance(child, Individual)
        assert child.parent_ids == [p1.id, p2.id]
        assert child.age == 0
        assert child.fitness == 0.0  # Not yet evaluated

    def test_evaluate_fitness(self, small_population, sample_fitness_function):
        """Test fitness evaluation."""
        individuals = list(small_population._individuals.values())[:3]
        evaluated = small_population.evaluate_fitness(individuals, sample_fitness_function)
        
        for ind in evaluated:
            assert ind.fitness > 0

    def test_replace_population_preserves_elites(self, small_population, sample_fitness_function):
        """Test that elites are preserved during replacement."""
        # Get current best
        current_best = max(small_population._individuals.values(), key=lambda x: x.fitness)
        
        # Create new offspring with lower fitness
        new_inds = []
        for _ in range(5):
            child = small_population.create_offspring(
                small_population.select_parent(),
                small_population.select_parent()
            )
            child.fitness = 0.1  # Lower than current best
            new_inds.append(child)
        
        small_population.replace_population(new_inds, sample_fitness_function)
        
        # Check that the best individual is still there (or better one)
        current_best_new = max(small_population._individuals.values(), key=lambda x: x.fitness)
        assert current_best_new.fitness >= current_best.fitness

    def test_replace_population_respects_max_size(self, small_population, sample_fitness_function):
        """Test that population size does not exceed max_size."""
        new_inds = [small_population.create_offspring(
            small_population.select_parent(),
            small_population.select_parent()
        ) for _ in range(50)]
        
        small_population.replace_population(new_inds, sample_fitness_function)
        
        assert len(small_population._individuals) <= small_population.max_size

class TestStatistics:
    """Tests for population statistics."""

    def test_get_stats_empty(self, empty_population):
        """Test stats on empty population."""
        stats = empty_population.get_stats()
        assert stats.size == 0
        assert stats.avg_fitness == 0.0

    def test_get_stats_populated(self, small_population):
        """Test stats on populated population."""
        stats = small_population.get_stats()
        assert stats.size == small_population.max_size
        assert stats.avg_fitness > 0
        assert stats.max_fitness >= stats.avg_fitness
        assert stats.min_fitness <= stats.avg_fitness
        assert stats.generation == 0

    def test_stats_includes_memory(self, small_population):
        """Test that stats include memory usage."""
        stats = small_population.get_stats()
        assert stats.memory_usage_mb >= 0

class TestPersistence:
    """Tests for saving and loading populations."""

    def test_save_and_load_population(self, small_population, tmp_path):
        """Test saving and loading a population."""
        filepath = tmp_path / "test_pop.json"
        small_population.save_population(str(filepath))
        
        assert filepath.exists()
        
        new_pop = Population(max_size=10)
        new_pop.load_population(str(filepath))
        
        assert len(new_pop._individuals) == len(small_population._individuals)
        assert new_pop.generation == small_population.generation

    def test_save_creates_directories(self, small_population, tmp_path):
        """Test that save creates parent directories if needed."""
        nested_path = tmp_path / "nested" / "deep" / "test_pop.json"
        small_population.save_population(str(nested_path))
        assert nested_path.exists()

class TestMemoryManagement:
    """Tests for memory management features."""

    def test_memory_threshold_check(self, small_population):
        """Test that memory check runs without error."""
        # This should not raise
        small_population._check_memory_usage()

    def test_memory_stats_accuracy(self, small_population):
        """Test that memory stats are reasonable."""
        stats = small_population.get_stats()
        # Memory should be positive but not absurdly large for a small pop
        assert 0 <= stats.memory_usage_mb < 1000
