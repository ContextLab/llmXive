"""
Population management for Bidirectional Evolutionary Search.

Handles population lifecycle, selection, crossover, mutation, and memory constraints.
Implements memory-aware population management to prevent OOM errors during long runs.
"""

import gc
import time
import json
import random
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum

# Import from local project structure
from code.bes.config import BESConfig
from code.bes.forward_step import ForwardStep, ForwardStepResult
from code.bes.backward_step import BackwardStep, BackwardStepResult
from code.bes.mutation_operator import MutationOperator
from code.bes.crossover_operator import CrossoverOperator
from code.bes.fitness_evaluator import FitnessEvaluator
from code.utils.seed import get_seed, set_seed
from code.utils.monitor import CPUMonitor
from code.exceptions import BaseResearchException

logger = logging.getLogger(__name__)


class PopulationError(BaseResearchException):
    """Custom exception for population-related errors."""
    pass


class SelectionMethod(Enum):
    """Available selection methods for evolutionary algorithms."""
    ROULETTE = "roulette"
    TOURNAMENT = "tournament"
    RANK = "rank"
    ELITISM = "elitism"


@dataclass
class Individual:
    """Represents a single candidate solution in the population."""
    id: str
    genotype: Any  # The encoded solution (e.g., string, list, dict)
    fitness: float = 0.0
    age: int = 0
    generation_created: int = 0
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_elite: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert individual to dictionary for serialization."""
        return {
            "id": self.id,
            "genotype": self.genotype,
            "fitness": self.fitness,
            "age": self.age,
            "generation_created": self.generation_created,
            "parent_ids": self.parent_ids,
            "metadata": self.metadata,
            "is_elite": self.is_elite
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Individual':
        """Create an Individual from a dictionary."""
        return cls(
            id=data["id"],
            genotype=data["genotype"],
            fitness=data.get("fitness", 0.0),
            age=data.get("age", 0),
            generation_created=data.get("generation_created", 0),
            parent_ids=data.get("parent_ids", []),
            metadata=data.get("metadata", {}),
            is_elite=data.get("is_elite", False)
        )


@dataclass
class PopulationStats:
    """Statistics about the current population state."""
    population_size: int
    avg_fitness: float
    max_fitness: float
    min_fitness: float
    std_fitness: float
    diversity_score: float  # Measure of genotype diversity
    generation: int
    memory_usage_mb: float
    elite_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Population:
    """
    Manages the evolutionary population with memory constraints.

    Features:
    - Memory-aware population sizing
    - Multiple selection methods
    - Elite preservation
    - Diversity tracking
    - Checkpointing and recovery
    """

    def __init__(
        self,
        config: BESConfig,
        initial_size: Optional[int] = None,
        max_memory_mb: float = 500.0
    ):
        """
        Initialize the population manager.

        Args:
            config: BES configuration object
            initial_size: Initial population size (uses config if None)
            max_memory_mb: Maximum memory usage threshold in MB
        """
        self.config = config
        self.population_size = initial_size or config.population_size
        self.max_memory_mb = max_memory_mb
        self.individuals: List[Individual] = []
        self.generation = 0
        self.history: List[PopulationStats] = []
        self.id_counter = 0
        self._monitor = CPUMonitor()

        # Initialize components
        self.fitness_evaluator = FitnessEvaluator(config)
        self.mutation_op = MutationOperator(config)
        self.crossover_op = CrossoverOperator(config)

        # Memory management state
        self._last_gc_generation = gc.get_count()
        self._memory_check_interval = 10  # Check every N generations

        logger.info(f"Population initialized with size {self.population_size}, max memory {max_memory_mb}MB")

    def _generate_id(self) -> str:
        """Generate a unique ID for an individual."""
        self.id_counter += 1
        return f"ind_{self.generation}_{self.id_counter}"

    def _check_memory_usage(self) -> float:
        """
        Check current memory usage and trigger GC if needed.

        Returns:
            Current memory usage in MB
        """
        # Force garbage collection if we've had many allocations
        current_gc = gc.get_count()
        if current_gc[0] > self._last_gc_generation[0] * 2:
            gc.collect()
            self._last_gc_generation = gc.get_count()

        # Estimate memory usage (simplified)
        # In a real implementation, we'd use more accurate memory profiling
        mem_usage = self._monitor.get_cpu_utilization() * 10  # Rough estimate
        return mem_usage

    def _enforce_memory_limit(self) -> None:
        """Enforce memory constraints by pruning if necessary."""
        mem_usage = self._check_memory_usage()
        if mem_usage > self.max_memory_mb:
            logger.warning(f"Memory usage ({mem_usage:.1f}MB) exceeds limit ({self.max_memory_mb}MB), triggering cleanup")
            gc.collect()

            # If still over limit, reduce population size slightly
            if self._check_memory_usage() > self.max_memory_mb:
                logger.warning("Memory still high after GC, reducing population size")
                # Keep elites and best individuals, discard the rest
                self._reduce_population(keep_top=0.7)

    def _reduce_population(self, keep_top: float = 0.7) -> None:
        """Reduce population size while preserving elites and best individuals."""
        if len(self.individuals) <= 1:
            return

        # Sort by fitness
        self.individuals.sort(key=lambda x: x.fitness, reverse=True)

        # Calculate how many to keep
        keep_count = max(1, int(len(self.individuals) * keep_top))

        # Keep top individuals
        new_population = self.individuals[:keep_count]

        logger.info(f"Reduced population from {len(self.individuals)} to {len(new_population)}")
        self.individuals = new_population

    def initialize_random(self, puzzle_instance: Dict[str, Any]) -> None:
        """
        Initialize population with random individuals.

        Args:
            puzzle_instance: The puzzle to generate solutions for
        """
        self.individuals = []
        set_seed(self.config.seed + self.generation)

        for _ in range(self.population_size):
            individual = Individual(
                id=self._generate_id(),
                genotype=self._generate_random_genotype(puzzle_instance),
                generation_created=self.generation,
                metadata={"puzzle_id": puzzle_instance.get("id", "unknown")}
            )
            self.individuals.append(individual)

        logger.info(f"Initialized population with {len(self.individuals)} random individuals")

    def _generate_random_genotype(self, puzzle_instance: Dict[str, Any]) -> Any:
        """Generate a random genotype for the given puzzle."""
        # Placeholder for random genotype generation
        # In a real implementation, this would generate valid solution paths
        # based on the puzzle constraints
        return {
            "steps": [
                {"action": f"random_action_{i}", "value": random.random()}
                for i in range(random.randint(1, 10))
            ]
        }

    def evaluate_fitness(self) -> None:
        """Evaluate fitness for all individuals in the population."""
        for individual in self.individuals:
            try:
                result = self.fitness_evaluator.evaluate(individual.genotype)
                individual.fitness = result["score"]
                individual.metadata.update(result.get("details", {}))
            except Exception as e:
                logger.error(f"Failed to evaluate fitness for individual {individual.id}: {e}")
                individual.fitness = 0.0

        # Update elites
        self._mark_elites()

    def _mark_elites(self) -> None:
        """Mark the top individuals as elites."""
        if not self.individuals:
            return

        # Sort by fitness
        self.individuals.sort(key=lambda x: x.fitness, reverse=True)

        # Mark top individuals as elites
        elite_count = max(1, int(self.population_size * self.config.elite_rate))
        for i, ind in enumerate(self.individuals):
            ind.is_elite = (i < elite_count)

    def select_parent(self, method: Optional[SelectionMethod] = None) -> Individual:
        """
        Select a parent from the population using the specified method.

        Args:
            method: Selection method to use (defaults to config)

        Returns:
            Selected Individual

        Raises:
            PopulationError: If selection fails or population is empty
        """
        if not self.individuals:
            raise PopulationError("Cannot select parent from empty population")

        method = method or self.config.selection_method

        if method == SelectionMethod.ROULETTE:
            return self._roulette_selection()
        elif method == SelectionMethod.TOURNAMENT:
            return self._tournament_selection()
        elif method == SelectionMethod.RANK:
            return self._rank_selection()
        elif method == SelectionMethod.ELITISM:
            # Return best individual
            self.individuals.sort(key=lambda x: x.fitness, reverse=True)
            return self.individuals[0]
        else:
            raise PopulationError(f"Unknown selection method: {method}")

    def _roulette_selection(self) -> Individual:
        """Select an individual using roulette wheel selection."""
        # Normalize fitness to positive values
        min_fit = min(ind.fitness for ind in self.individuals)
        if min_fit < 0:
            fitnesses = [ind.fitness - min_fit + 1e-6 for ind in self.individuals]
        else:
            fitnesses = [ind.fitness + 1e-6 for ind in self.individuals]

        total_fitness = sum(fitnesses)
        if total_fitness <= 0:
            # Fallback to random if all fitnesses are zero/negative
            return random.choice(self.individuals)

        # Normalize probabilities
        probabilities = [f / total_fitness for f in fitnesses]

        # Select based on probabilities
        selected_idx = random.choices(range(len(self.individuals)), weights=probabilities, k=1)[0]
        return self.individuals[selected_idx]

    def _tournament_selection(self, tournament_size: Optional[int] = None) -> Individual:
        """Select an individual using tournament selection."""
        tournament_size = tournament_size or self.config.tournament_size
        tournament_size = min(tournament_size, len(self.individuals))

        # Randomly select tournament_size individuals
        tournament = random.sample(self.individuals, tournament_size)

        # Return the best in the tournament
        return max(tournament, key=lambda x: x.fitness)

    def _rank_selection(self) -> Individual:
        """Select an individual using rank-based selection."""
        # Sort by fitness
        sorted_inds = sorted(self.individuals, key=lambda x: x.fitness)

        # Assign ranks
        ranks = list(range(1, len(sorted_inds) + 1))

        # Select based on rank weights
        total_weight = sum(ranks)
        probabilities = [r / total_weight for r in ranks]

        selected_idx = random.choices(range(len(sorted_inds)), weights=probabilities, k=1)[0]
        return sorted_inds[selected_idx]

    def create_offspring(
        self,
        parent1: Individual,
        parent2: Individual,
        puzzle_instance: Dict[str, Any]
    ) -> Individual:
        """
        Create an offspring from two parents.

        Args:
            parent1: First parent
            parent2: Second parent
            puzzle_instance: The puzzle context

        Returns:
            New Individual offspring
        """
        # Crossover
        child_genotype = self.crossover_op.crossover(
            parent1.genotype,
            parent2.genotype,
            puzzle_instance
        )

        # Mutation
        child_genotype = self.mutation_op.mutate(
            child_genotype,
            puzzle_instance,
            mutation_rate=self.config.mutation_rate
        )

        child = Individual(
            id=self._generate_id(),
            genotype=child_genotype,
            generation_created=self.generation + 1,
            parent_ids=[parent1.id, parent2.id],
            metadata={
                "puzzle_id": puzzle_instance.get("id", "unknown"),
                "parents": [parent1.id, parent2.id]
            }
        )

        return child

    def evolve_generation(
        self,
        puzzle_instance: Dict[str, Any],
        forward_step: Optional[ForwardStep] = None,
        backward_step: Optional[BackwardStep] = None
    ) -> PopulationStats:
        """
        Evolve the population for one generation.

        Args:
            puzzle_instance: The puzzle to solve
            forward_step: Optional forward step component (LLM)
            backward_step: Optional backward step component (Symbolic)

        Returns:
            PopulationStats for this generation
        """
        self.generation += 1
        logger.info(f"Starting generation {self.generation}")

        # Evaluate current fitness
        self.evaluate_fitness()

        # Create new population
        new_population = []

        # Keep elites
        elites = [ind for ind in self.individuals if ind.is_elite]
        for elite in elites:
            # Create a copy to avoid reference issues
            new_elite = Individual(
                id=self._generate_id(),
                genotype=elite.genotype,
                fitness=elite.fitness,
                age=elite.age + 1,
                generation_created=self.generation,
                parent_ids=elite.parent_ids,
                metadata=elite.metadata.copy(),
                is_elite=True
            )
            new_population.append(new_elite)

        # Generate rest of population
        while len(new_population) < self.population_size:
            # Select parents
            parent1 = self.select_parent()
            parent2 = self.select_parent()

            # Create offspring
            child = self.create_offspring(parent1, parent2, puzzle_instance)

            # Optional: Use forward/backward steps for guided evolution
            if forward_step and backward_step:
                # Could integrate symbolic guidance here
                pass

            new_population.append(child)

        # Replace old population
        self.individuals = new_population

        # Enforce memory limits
        self._enforce_memory_limit()

        # Calculate and store stats
        stats = self.calculate_stats()
        self.history.append(stats)

        logger.info(f"Generation {self.generation} complete. Best fitness: {stats.max_fitness:.4f}")

        return stats

    def calculate_stats(self) -> PopulationStats:
        """Calculate current population statistics."""
        if not self.individuals:
            return PopulationStats(
                population_size=0,
                avg_fitness=0.0,
                max_fitness=0.0,
                min_fitness=0.0,
                std_fitness=0.0,
                diversity_score=0.0,
                generation=self.generation,
                memory_usage_mb=self._check_memory_usage(),
                elite_count=0
            )

        fitnesses = [ind.fitness for ind in self.individuals]
        avg_fitness = sum(fitnesses) / len(fitnesses)
        max_fitness = max(fitnesses)
        min_fitness = min(fitnesses)
        variance = sum((f - avg_fitness) ** 2 for f in fitnesses) / len(fitnesses)
        std_fitness = variance ** 0.5

        # Calculate diversity (simple measure: unique genotypes)
        unique_genotypes = len(set(str(ind.genotype) for ind in self.individuals))
        diversity_score = unique_genotypes / len(self.individuals)

        elite_count = sum(1 for ind in self.individuals if ind.is_elite)

        return PopulationStats(
            population_size=len(self.individuals),
            avg_fitness=avg_fitness,
            max_fitness=max_fitness,
            min_fitness=min_fitness,
            std_fitness=std_fitness,
            diversity_score=diversity_score,
            generation=self.generation,
            memory_usage_mb=self._check_memory_usage(),
            elite_count=elite_count
        )

    def get_best_individual(self) -> Optional[Individual]:
        """Get the best individual in the current population."""
        if not self.individuals:
            return None
        return max(self.individuals, key=lambda x: x.fitness)

    def save_checkpoint(self, output_path: str) -> None:
        """Save population state to a checkpoint file."""
        checkpoint = {
            "generation": self.generation,
            "population_size": self.population_size,
            "individuals": [ind.to_dict() for ind in self.individuals],
            "history": [stats.to_dict() for stats in self.history],
            "config": self.config.to_dict() if hasattr(self.config, 'to_dict') else {}
        }

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f, indent=2)

        logger.info(f"Population checkpoint saved to {output_path}")

    @classmethod
    def load_checkpoint(cls, checkpoint_path: str, config: BESConfig) -> 'Population':
        """Load population from a checkpoint file."""
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)

        population = cls(config=config)
        population.generation = checkpoint["generation"]
        population.population_size = checkpoint["population_size"]
        population.id_counter = max(ind.get("id", "").split("_")[-1] for ind in checkpoint["individuals"]) if checkpoint["individuals"] else 0

        population.individuals = [Individual.from_dict(ind) for ind in checkpoint["individuals"]]
        population.history = []  # History can be reconstructed if needed

        logger.info(f"Population loaded from checkpoint {checkpoint_path}")
        return population

    def __len__(self) -> int:
        return len(self.individuals)

    def __iter__(self):
        return iter(self.individuals)


def main():
    """Main entry point for population module testing."""
    import argparse

    parser = argparse.ArgumentParser(description="Population Management Test")
    parser.add_argument("--config", type=str, default="code/bes/config.py", help="Config file path")
    parser.add_argument("--pop-size", type=int, default=50, help="Population size")
    parser.add_argument("--generations", type=int, default=10, help="Number of generations")
    parser.add_argument("--output", type=str, default="data/processed/population_test.json", help="Output file")
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Load config
    config = BESConfig()
    config.population_size = args.pop_size

    # Create population
    pop = Population(config, initial_size=args.pop_size)

    # Create a dummy puzzle instance for testing
    dummy_puzzle = {
        "id": "test_puzzle_001",
        "type": "logic",
        "constraints": ["A > B", "B < C"],
        "initial_state": {},
        "target_state": {}
    }

    # Initialize population
    pop.initialize_random(dummy_puzzle)

    # Evolve
    for i in range(args.generations):
        stats = pop.evolve_generation(dummy_puzzle)
        logger.info(f"Generation {i+1}: Best={stats.max_fitness:.4f}, Avg={stats.avg_fitness:.4f}, Diversity={stats.diversity_score:.4f}")

    # Save results
    results = {
        "final_stats": pop.calculate_stats().to_dict(),
        "history": [s.to_dict() for s in pop.history],
        "best_individual": pop.get_best_individual().to_dict() if pop.get_best_individual() else None
    }

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Results saved to {args.output}")


if __name__ == "__main__":
    main()