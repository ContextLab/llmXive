"""
Unit tests for the Population management module.
"""

import pytest
import json
import tempfile
from pathlib import Path
import numpy as np

from code.bes.population import Population, Individual, PopulationStats, PopulationError


@pytest.fixture
def sample_population():
    """Create a sample population for testing."""
    pop = Population(max_size=50, min_size=10, seed=42)

    def initializer(seed_val):
        import random
        random.seed(seed_val)
        return {
            "values": [random.uniform(-1, 1) for _ in range(5)],
            "type": random.choice(["A", "B", "C"])
        }

    pop.initialize(initializer_fn=initializer, count=20)
    return pop


def test_population_initialization():
    """Test that population initializes correctly."""
    pop = Population(max_size=100, min_size=10, seed=123)

    def simple_init(seed_val):
        return {"seed": seed_val}

    pop.initialize(simple_init, count=15)

    assert len(pop) == 15
    assert pop.generation == 0
    assert pop.seed == 123

    # Check all individuals have unique IDs
    ids = [ind.id for ind in pop.individuals]
    assert len(ids) == len(set(ids))


def test_population_fitness_evaluation(sample_population):
    """Test fitness evaluation."""
    def evaluator(ind):
        values = ind.genotype.get("values", [])
        return sum(values)

    sample_population.evaluate_fitness(evaluator)

    # All individuals should have fitness >= 0 (since we didn't set negative)
    for ind in sample_population.individuals:
        assert ind.fitness is not None
        assert ind.age == 1


def test_population_selection(sample_population):
    """Test parent selection."""
    def evaluator(ind):
        values = ind.genotype.get("values", [])
        return sum(values)

    sample_population.evaluate_fitness(evaluator)
    parents = sample_population.select_parents(count=5)

    assert len(parents) == 5
    assert all(isinstance(p, Individual) for p in parents)


def test_population_reproduction(sample_population):
    """Test reproduction creates new generation."""
    def evaluator(ind):
        values = ind.genotype.get("values", [])
        return sum(values)

    sample_population.evaluate_fitness(evaluator)

    parents = sample_population.select_parents(count=10)

    def crossover(p1, p2):
        child1 = Individual(
            id=f"child1_{p1.id}",
            genotype={**p1.genotype, **p2.genotype},
            parent_ids=[p1.id, p2.id]
        )
        child2 = Individual(
            id=f"child2_{p1.id}",
            genotype={**p2.genotype, **p1.genotype},
            parent_ids=[p2.id, p1.id]
        )
        return child1, child2

    def mutate(ind):
        new_genotype = ind.genotype.copy()
        if "values" in new_genotype:
            new_genotype["values"] = [v * 1.1 for v in new_genotype["values"]]
        return Individual(
            id=ind.id,
            genotype=new_genotype,
            parent_ids=ind.parent_ids
        )

    new_pop = sample_population.reproduce(
        parents=parents,
        crossover_fn=crossover,
        mutation_fn=mutate,
        mutation_rate=0.5
    )

    assert len(new_pop) > 0
    assert sample_population.generation == 1


def test_population_get_best(sample_population):
    """Test getting the best individual."""
    def evaluator(ind):
        return float(ind.genotype.get("values", [0])[0])

    sample_population.evaluate_fitness(evaluator)

    best = sample_population.get_best()
    assert best is not None
    assert best.fitness == max(ind.fitness for ind in sample_population.individuals)


def test_population_statistics(sample_population):
    """Test population statistics calculation."""
    def evaluator(ind):
        values = ind.genotype.get("values", [])
        return sum(values)

    sample_population.evaluate_fitness(evaluator)

    stats = sample_population.get_statistics()

    assert stats.generation == 0
    assert stats.size == len(sample_population.individuals)
    assert stats.avg_fitness is not None
    assert stats.best_fitness is not None
    assert stats.worst_fitness is not None
    assert stats.std_fitness >= 0


def test_population_save_and_load(sample_population):
    """Test saving and loading population state."""
    def evaluator(ind):
        return float(ind.genotype.get("values", [0])[0])

    sample_population.evaluate_fitness(evaluator)
    sample_population.get_statistics()  # Add to history

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = Path(f.name)

    try:
        sample_population.save_to_file(temp_path)

        # Verify file exists and is valid JSON
        assert temp_path.exists()
        with open(temp_path, 'r') as f:
            data = json.load(f)
        assert "individuals" in data
        assert "generation" in data

        # Load into new population
        new_pop = Population(max_size=100, min_size=10)
        new_pop.load_from_file(temp_path)

        assert new_pop.generation == sample_population.generation
        assert len(new_pop.individuals) == len(sample_population.individuals)

    finally:
        temp_path.unlink()


def test_population_memory_pruning():
    """Test that population prunes when memory pressure is high."""
    pop = Population(max_size=10, min_size=3, memory_threshold_mb=0.001, seed=42)

    def initializer(seed_val):
        import random
        random.seed(seed_val)
        # Create large genotype to trigger memory pressure
        return {"large_data": "x" * 10000, "value": seed_val}

    pop.initialize(initializer_fn=initializer, count=10)

    def evaluator(ind):
        return ind.genotype["value"]

    pop.evaluate_fitness(evaluator)

    # Select and reproduce to trigger pruning
    parents = pop.select_parents(count=5)

    def simple_crossover(p1, p2):
        return p1, p2

    def simple_mutate(ind):
        return ind

    pop.reproduce(
        parents=parents,
        crossover_fn=simple_crossover,
        mutation_fn=simple_mutate,
        mutation_rate=0.0
    )

    # Population should have been pruned
    assert len(pop.individuals) <= pop.max_size
    assert len(pop.individuals) >= pop.min_size


def test_population_empty_population():
    """Test behavior with empty population."""
    pop = Population(max_size=10, min_size=2)

    assert len(pop) == 0
    assert pop.get_best() is None

    stats = pop.get_statistics()
    assert stats.size == 0
    assert stats.avg_fitness == 0.0


def test_population_tournament_selection():
    """Test tournament selection specifically."""
    pop = Population(max_size=50, min_size=10, seed=42)

    def initializer(seed_val):
        import random
        random.seed(seed_val)
        return {"value": seed_val}

    pop.initialize(initializer_fn=initializer, count=20)

    def evaluator(ind):
        return ind.genotype["value"]

    pop.evaluate_fitness(evaluator)

    # Select using tournament
    parents = pop.select_parents(count=5)

    assert len(parents) == 5
    # Tournament should favor higher fitness
    assert all(isinstance(p, Individual) for p in parents)


def test_population_elitism():
    """Test that elitism preserves best individuals."""
    pop = Population(max_size=50, min_size=10, seed=42)

    def initializer(seed_val):
        import random
        random.seed(seed_val)
        return {"value": seed_val}

    pop.initialize(initializer_fn=initializer, count=20)

    def evaluator(ind):
        return ind.genotype["value"]

    pop.evaluate_fitness(evaluator)

    best_before = pop.get_best()
    best_fitness_before = best_before.fitness

    parents = pop.select_parents(count=10)

    def simple_crossover(p1, p2):
        return p1, p2

    def simple_mutate(ind):
        return ind

    pop.reproduce(
        parents=parents,
        crossover_fn=simple_crossover,
        mutation_fn=simple_mutate,
        mutation_rate=0.0,
        elitism_count=3
    )

    best_after = pop.get_best()
    assert best_after.fitness >= best_fitness_before


def test_population_diversity_metric():
    """Test diversity metric calculation."""
    pop = Population(max_size=50, min_size=10, seed=42)

    def initializer(seed_val):
        import random
        random.seed(seed_val)
        return {"unique": seed_val, "common": 1}

    pop.initialize(initializer_fn=initializer, count=20)

    stats = pop.get_statistics()
    assert stats.diversity_metric >= 0
    assert stats.diversity_metric <= 1  # Normalized metric


def test_population_error_on_too_small():
    """Test error when population too small for selection."""
    pop = Population(max_size=50, min_size=2, seed=42)

    def initializer(seed_val):
        return {"value": seed_val}

    pop.initialize(initializer_fn=initializer, count=1)

    with pytest.raises(PopulationError):
        pop.select_parents(count=2)