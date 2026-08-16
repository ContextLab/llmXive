"""
Population management for the Bidirectional Evolutionary Search (BES).

This module handles the evolutionary population, including:
- Initialization of individuals
- Selection, crossover, and mutation operations
- Memory management to stay under thresholds
- Tracking of best individuals and diversity metrics
"""

import gc
import time
import json
import random
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
import numpy as np

from code.utils.logger import log
from code.utils.seed import get_seed
from code.exceptions import BaseResearchException


class PopulationError(BaseResearchException):
    """Base exception for population-related errors."""
    pass


@dataclass
class Individual:
    """Represents a single individual in the evolutionary population."""
    id: str
    genotype: Dict[str, Any]  # The encoded solution/strategy
    phenotype: Optional[Dict[str, Any]] = None  # The decoded/realized solution
    fitness: float = -1.0
    age: int = 0
    generation_created: int = 0
    parent_ids: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.parent_ids is None:
            self.parent_ids = []


@dataclass
class PopulationStats:
    """Statistics about the current population state."""
    generation: int
    size: int
    avg_fitness: float
    best_fitness: float
    worst_fitness: float
    std_fitness: float
    diversity_metric: float  # e.g., average pairwise genotype distance
    memory_usage_mb: float
    timestamp: float


class Population:
    """
    Manages the evolutionary population for BES.

    Implements memory-aware population management to ensure the system
    stays within resource constraints while maintaining evolutionary pressure.
    """

    def __init__(
        self,
        max_size: int = 100,
        min_size: int = 20,
        memory_threshold_mb: float = 500.0,
        seed: Optional[int] = None
    ):
        """
        Initialize the population manager.

        Args:
            max_size: Maximum number of individuals allowed
            min_size: Minimum number of individuals to maintain
            memory_threshold_mb: Soft memory limit in MB
            seed: Random seed for reproducibility
        """
        self.max_size = max_size
        self.min_size = min_size
        self.memory_threshold_mb = memory_threshold_mb
        self.seed = seed if seed is not None else get_seed()
        random.seed(self.seed)

        self.individuals: List[Individual] = []
        self.generation = 0
        self.id_counter = 0
        self.history: List[PopulationStats] = []

        log(f"Population initialized: max_size={max_size}, min_size={min_size}, "
            f"memory_threshold={memory_threshold_mb}MB, seed={self.seed}")

    def _generate_id(self) -> str:
        """Generate a unique ID for an individual."""
        self.id_counter += 1
        return f"ind_{self.generation}_{self.id_counter}"

    def _calculate_memory_usage(self) -> float:
        """Estimate current memory usage in MB."""
        # Simple heuristic: sum of genotype sizes + overhead
        total_size = 0
        for ind in self.individuals:
            # Convert genotype to JSON string to estimate size
            try:
                json_str = json.dumps(ind.genotype)
                total_size += len(json_str)
            except (TypeError, ValueError):
                # Fallback for non-serializable genotypes
                total_size += 1000  # Estimate

        # Estimate: 1 byte per char + 10% overhead
        total_bytes = total_size * 1.1
        return total_bytes / (1024 * 1024)

    def _check_memory_pressure(self) -> bool:
        """Check if we're approaching memory limits."""
        current_usage = self._calculate_memory_usage()
        return current_usage > (self.memory_threshold_mb * 0.8)

    def initialize(
        self,
        initializer_fn: Callable[[int], Dict[str, Any]],
        count: Optional[int] = None
    ) -> None:
        """
        Initialize the population with random individuals.

        Args:
            initializer_fn: Function that takes a random seed and returns a genotype
            count: Number of individuals to create (defaults to min_size)
        """
        if count is None:
            count = self.min_size

        count = min(count, self.max_size)
        self.individuals = []
        self.id_counter = 0
        self.generation = 0

        for _ in range(count):
            seed_val = random.randint(0, 2**31 - 1)
            genotype = initializer_fn(seed_val)
            individual = Individual(
                id=self._generate_id(),
                genotype=genotype,
                generation_created=0
            )
            self.individuals.append(individual)

        log(f"Population initialized with {len(self.individuals)} individuals")

    def evaluate_fitness(
        self,
        evaluator_fn: Callable[[Individual], float],
        verbose: bool = False
    ) -> None:
        """
        Evaluate fitness for all individuals in the population.

        Args:
            evaluator_fn: Function that takes an Individual and returns fitness score
            verbose: Whether to log individual scores
        """
        for ind in self.individuals:
            try:
                ind.fitness = evaluator_fn(ind)
                ind.age += 1
                if verbose:
                    log(f"Evaluated {ind.id}: fitness={ind.fitness:.4f}")
            except Exception as e:
                log(f"Error evaluating individual {ind.id}: {e}", level="ERROR")
                ind.fitness = float('-inf')

    def select_parents(
        self,
        count: int,
        selection_fn: Optional[Callable[[List[Individual]], Individual]] = None
    ) -> List[Individual]:
        """
        Select parents for the next generation.

        Args:
            count: Number of parents to select
            selection_fn: Custom selection function (defaults to tournament selection)

        Returns:
            List of selected parent individuals
        """
        if len(self.individuals) < 2:
            raise PopulationError("Population too small for selection")

        if selection_fn is None:
            selection_fn = self._tournament_selection

        parents = []
        for _ in range(count):
            parent = selection_fn(self.individuals)
            parents.append(parent)

        return parents

    def _tournament_selection(
        self,
        population: List[Individual],
        k: int = 3
    ) -> Individual:
        """Tournament selection with size k."""
        candidates = random.sample(population, min(k, len(population)))
        return max(candidates, key=lambda ind: ind.fitness)

    def reproduce(
        self,
        parents: List[Individual],
        crossover_fn: Callable[[Individual, Individual], Tuple[Individual, Individual]],
        mutation_fn: Callable[[Individual], Individual],
        mutation_rate: float = 0.1,
        elitism_count: int = 2
    ) -> List[Individual]:
        """
        Create the next generation through reproduction.

        Args:
            parents: List of parent individuals
            crossover_fn: Function that performs crossover
            mutation_fn: Function that performs mutation
            mutation_rate: Probability of mutation per individual
            elitism_count: Number of best individuals to preserve

        Returns:
            New population for the next generation
        """
        new_population = []

        # Elitism: preserve best individuals
        sorted_by_fitness = sorted(self.individuals, key=lambda x: x.fitness, reverse=True)
        for i in range(min(elitism_count, len(sorted_by_fitness))):
            elite = sorted_by_fitness[i]
            new_elite = Individual(
                id=self._generate_id(),
                genotype=elite.genotype.copy(),
                phenotype=elite.phenotype.copy() if elite.phenotype else None,
                fitness=elite.fitness,
                generation_created=self.generation + 1,
                parent_ids=[elite.id],
                metadata=elite.metadata.copy()
            )
            new_population.append(new_elite)

        # Generate rest of population
        target_size = min(self.max_size, self.min(max(elitism_count + 1, len(self.individuals)), self.max_size))
        while len(new_population) < target_size:
            if len(parents) < 2:
                # Fallback: clone a random individual
                parent = random.choice(self.individuals)
                child = Individual(
                    id=self._generate_id(),
                    genotype=parent.genotype.copy(),
                    generation_created=self.generation + 1,
                    parent_ids=[parent.id]
                )
            else:
                parent1, parent2 = random.sample(parents, 2)
                child1, child2 = crossover_fn(parent1, parent2)
                child = child1

            # Apply mutation
            if random.random() < mutation_rate:
                child = mutation_fn(child)

            child.generation_created = self.generation + 1
            new_population.append(child)

        self.individuals = new_population
        self.generation += 1

        # Memory management
        if self._check_memory_pressure():
            self._prune_low_fitness(percentage=0.2)

        return self.individuals

    def _prune_low_fitness(self, percentage: float = 0.2) -> None:
        """Remove the lowest fitness individuals to manage memory."""
        if len(self.individuals) <= self.min_size:
            return

        remove_count = max(1, int(len(self.individuals) * percentage))
        sorted_by_fitness = sorted(self.individuals, key=lambda x: x.fitness)

        # Keep only the best individuals
        keep_count = len(self.individuals) - remove_count
        self.individuals = sorted_by_fitness[-keep_count:]

        log(f"Pruned {remove_count} low-fitness individuals. New size: {len(self.individuals)}")

        # Force garbage collection
        gc.collect()

    def get_best(self) -> Optional[Individual]:
        """Return the best individual in the current population."""
        if not self.individuals:
            return None
        return max(self.individuals, key=lambda x: x.fitness)

    def get_statistics(self) -> PopulationStats:
        """Calculate and return current population statistics."""
        if not self.individuals:
            return PopulationStats(
                generation=self.generation,
                size=0,
                avg_fitness=0.0,
                best_fitness=0.0,
                worst_fitness=0.0,
                std_fitness=0.0,
                diversity_metric=0.0,
                memory_usage_mb=0.0,
                timestamp=time.time()
            )

        fitnesses = [ind.fitness for ind in self.individuals if ind.fitness >= 0]
        if not fitnesses:
            fitnesses = [0.0]

        avg_fitness = np.mean(fitnesses)
        best_fitness = max(fitnesses)
        worst_fitness = min(fitnesses)
        std_fitness = np.std(fitnesses)

        # Simple diversity metric: average pairwise genotype hash difference
        diversity = self._calculate_diversity()

        stats = PopulationStats(
            generation=self.generation,
            size=len(self.individuals),
            avg_fitness=float(avg_fitness),
            best_fitness=float(best_fitness),
            worst_fitness=float(worst_fitness),
            std_fitness=float(std_fitness),
            diversity_metric=float(diversity),
            memory_usage_mb=self._calculate_memory_usage(),
            timestamp=time.time()
        )

        self.history.append(stats)
        return stats

    def _calculate_diversity(self) -> float:
        """Calculate a simple diversity metric based on genotype hashes."""
        if len(self.individuals) < 2:
            return 0.0

        hashes = []
        for ind in self.individuals:
            try:
                h = hash(json.dumps(ind.genotype, sort_keys=True))
                hashes.append(h)
            except (TypeError, ValueError):
                hashes.append(hash(str(ind.genotype)))

        # Normalize hashes to [0, 1] and calculate variance
        normalized = [(h % 10000) / 10000.0 for h in hashes]
        variance = np.var(normalized)
        return float(np.sqrt(variance))

    def save_to_file(self, filepath: Path) -> None:
        """Save the current population state to a file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "generation": self.generation,
            "seed": self.seed,
            "max_size": self.max_size,
            "min_size": self.min_size,
            "individuals": [
                {
                    "id": ind.id,
                    "genotype": ind.genotype,
                    "phenotype": ind.phenotype,
                    "fitness": ind.fitness,
                    "age": ind.age,
                    "generation_created": ind.generation_created,
                    "parent_ids": ind.parent_ids,
                    "metadata": ind.metadata
                }
                for ind in self.individuals
            ],
            "history": [asdict(stats) for stats in self.history]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        log(f"Population saved to {filepath}")

    def load_from_file(self, filepath: Path) -> None:
        """Load population state from a file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise PopulationError(f"Population file not found: {filepath}")

        with open(filepath, 'r') as f:
            data = json.load(f)

        self.generation = data["generation"]
        self.seed = data.get("seed", self.seed)
        self.max_size = data.get("max_size", self.max_size)
        self.min_size = data.get("min_size", self.min_size)

        self.individuals = []
        for ind_data in data["individuals"]:
            individual = Individual(
                id=ind_data["id"],
                genotype=ind_data["genotype"],
                phenotype=ind_data.get("phenotype"),
                fitness=ind_data["fitness"],
                age=ind_data["age"],
                generation_created=ind_data["generation_created"],
                parent_ids=ind_data.get("parent_ids", []),
                metadata=ind_data.get("metadata", {})
            )
            self.individuals.append(individual)

        self.history = [PopulationStats(**stats) for stats in data.get("history", [])]

        log(f"Population loaded from {filepath}")

    def __len__(self) -> int:
        return len(self.individuals)

    def __iter__(self):
        return iter(self.individuals)


def main():
    """Main entry point for population management demonstration."""
    import argparse

    parser = argparse.ArgumentParser(description="Population management for BES")
    parser.add_argument("--max-size", type=int, default=100, help="Max population size")
    parser.add_argument("--min-size", type=int, default=20, help="Min population size")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/processed/population_state.json",
                      help="Output file path")
    args = parser.parse_args()

    # Initialize population
    pop = Population(
        max_size=args.max_size,
        min_size=args.min_size,
        seed=args.seed
    )

    # Simple initializer for demonstration
    def simple_initializer(seed_val: int) -> Dict[str, Any]:
        random.seed(seed_val)
        return {
            "params": [random.uniform(-1, 1) for _ in range(10)],
            "strategy": random.choice(["greedy", "random", "balanced"]),
            "threshold": random.uniform(0, 1)
        }

    # Initialize with random individuals
    pop.initialize(initializer_fn=simple_initializer, count=pop.min_size)

    # Simple fitness evaluator
    def simple_evaluator(ind: Individual) -> float:
        params = ind.genotype.get("params", [])
        return sum(p**2 for p in params)  # Simple quadratic function

    # Evaluate fitness
    pop.evaluate_fitness(evaluator_fn=simple_evaluator)

    # Get statistics
    stats = pop.get_statistics()
    log(f"Initial stats: avg_fitness={stats.avg_fitness:.4f}, best={stats.best_fitness:.4f}")

    # Save population
    pop.save_to_file(Path(args.output))
    log(f"Population state saved to {args.output}")

    # Demonstrate reproduction
    parents = pop.select_parents(count=10)
    new_pop = pop.reproduce(
        parents=parents,
        crossover_fn=lambda p1, p2: (
            Individual(id=f"child_{p1.id}_{p2.id}", genotype={**p1.genotype, **p2.genotype}),
            Individual(id=f"child_{p2.id}_{p1.id}", genotype={**p2.genotype, **p1.genotype})
        ),
        mutation_fn=lambda ind: Individual(
            id=ind.id,
            genotype={k: v * 1.1 for k, v in ind.genotype.items() if isinstance(v, (int, float))}
        ),
        mutation_rate=0.1
    )

    new_stats = pop.get_statistics()
    log(f"After reproduction: avg_fitness={new_stats.avg_fitness:.4f}, best={new_stats.best_fitness:.4f}")

    # Save final state
    pop.save_to_file(Path(args.output))

    return pop


if __name__ == "__main__":
    main()
