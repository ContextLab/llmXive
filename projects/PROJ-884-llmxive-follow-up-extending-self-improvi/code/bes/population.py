"""
Population management for the Bidirectional Evolutionary Search (BES) framework.

This module handles the evolutionary population, including individual representation,
selection, replacement, and memory management to ensure the population stays within
manageable resource thresholds.
"""

import gc
import time
import json
import random
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum

# Import from project structure
from code.exceptions import BaseResearchException
from code.utils.seed import get_seed, set_seed
from code.utils.logger import log
from code.bes.forward_step import ForwardStepResult
from code.bes.backward_step import BackwardStepResult


class PopulationError(BaseResearchException):
    """Base exception for population-related errors."""
    pass


class SelectionMethod(Enum):
    """Available selection methods for the evolutionary algorithm."""
    TOURNAMENT = "tournament"
    RANK = "rank"
    ROUNDR_ROBIN = "round_robin"
    ELITE = "elite"


@dataclass
class Individual:
    """
    Represents a single individual in the evolutionary population.
    
    Attributes:
        id: Unique identifier for this individual.
        genotype: The solution representation (e.g., list of moves, path).
        phenotype: The interpreted solution (e.g., final state, trajectory).
        fitness: The fitness score (higher is better).
        age: Number of generations this individual has survived.
        parent_ids: IDs of parent individuals (for lineage tracking).
        metadata: Additional data for analysis (e.g., generation created, source).
    """
    id: str
    genotype: Any
    phenotype: Any
    fitness: float
    age: int = 0
    parent_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not isinstance(self.id, str):
            self.id = str(self.id)
        if self.parent_ids is None:
            self.parent_ids = []
        if self.metadata is None:
            self.metadata = {}

    def __repr__(self):
        return f"Individual(id={self.id}, fitness={self.fitness:.4f}, age={self.age})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert individual to a dictionary for serialization."""
        return {
            "id": self.id,
            "genotype": self.genotype,
            "phenotype": self.phenotype,
            "fitness": self.fitness,
            "age": self.age,
            "parent_ids": self.parent_ids,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Individual":
        """Create an Individual from a dictionary."""
        return cls(
            id=data["id"],
            genotype=data["genotype"],
            phenotype=data["phenotype"],
            fitness=data["fitness"],
            age=data.get("age", 0),
            parent_ids=data.get("parent_ids", []),
            metadata=data.get("metadata", {})
        )

@dataclass
class PopulationStats:
    """Statistics about the current population state."""
    size: int
    avg_fitness: float
    max_fitness: float
    min_fitness: float
    std_fitness: float
    avg_age: float
    diversity_score: float  # Placeholder for diversity metric
    generation: int
    memory_usage_mb: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size": self.size,
            "avg_fitness": self.avg_fitness,
            "max_fitness": self.max_fitness,
            "min_fitness": self.min_fitness,
            "std_fitness": self.std_fitness,
            "avg_age": self.avg_age,
            "diversity_score": self.diversity_score,
            "generation": self.generation,
            "memory_usage_mb": self.memory_usage_mb
        }

class Population:
    """
    Manages the evolutionary population with memory-aware constraints.
    
    This class implements:
    - Population initialization
    - Selection mechanisms (tournament, rank, etc.)
    - Replacement strategies (elitism, generational)
    - Memory management (garbage collection, size limits)
    - Statistics tracking
    """
    
    def __init__(
        self,
        max_size: int = 100,
        min_size: int = 10,
        elite_count: int = 2,
        selection_method: SelectionMethod = SelectionMethod.TOURNAMENT,
        tournament_size: int = 3,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        memory_threshold_mb: float = 500.0,
        generation: int = 0
    ):
        """
        Initialize the population manager.
        
        Args:
            max_size: Maximum number of individuals allowed.
            min_size: Minimum number of individuals before regeneration.
            elite_count: Number of top individuals to preserve each generation.
            selection_method: Method for selecting parents.
            tournament_size: Size for tournament selection.
            mutation_rate: Probability of mutation per gene.
            crossover_rate: Probability of crossover between parents.
            memory_threshold_mb: Soft limit on memory usage (triggers GC).
            generation: Starting generation number.
        """
        self.max_size = max_size
        self.min_size = min_size
        self.elite_count = min(elite_count, max_size)
        self.selection_method = selection_method
        self.tournament_size = tournament_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.memory_threshold_mb = memory_threshold_mb
        self.generation = generation
        
        self._individuals: Dict[str, Individual] = {}
        self._id_counter: int = 0
        self._history: List[Dict[str, Any]] = []
        
        # Ensure we don't start with invalid parameters
        if self.elite_count > self.max_size:
            raise PopulationError(f"elite_count ({self.elite_count}) cannot exceed max_size ({self.max_size})")
        if self.tournament_size > self.max_size:
            self.tournament_size = max(2, self.max_size)
    
    def _generate_id(self) -> str:
        """Generate a unique ID for a new individual."""
        self._id_counter += 1
        return f"ind_{self.generation}_{self._id_counter}"
    
    def initialize(
        self,
        initial_genotypes: Optional[List[Any]] = None,
        fitness_function: Optional[Callable[[Individual], float]] = None,
        seed: Optional[int] = None
    ) -> List[Individual]:
        """
        Initialize the population with random or provided genotypes.
        
        Args:
            initial_genotypes: Optional list of initial genotypes. If None, random ones are generated.
            fitness_function: Function to evaluate fitness. If None, fitness is 0.0.
            seed: Optional random seed for reproducibility.
        
        Returns:
            List of initialized individuals.
        """
        if seed is not None:
            set_seed(seed)
        
        self._individuals.clear()
        self._id_counter = 0
        self.generation = 0
        
        if initial_genotypes:
            # Use provided genotypes
            for genotype in initial_genotypes[:self.max_size]:
                ind = Individual(
                    id=self._generate_id(),
                    genotype=genotype,
                    phenotype=genotype,  # Default phenotype = genotype
                    fitness=0.0,
                    age=0,
                    metadata={"source": "initial"}
                )
                if fitness_function:
                    ind.fitness = fitness_function(ind)
                self._individuals[ind.id] = ind
        else:
            # Generate random genotypes (placeholder logic - should be overridden by specific puzzle types)
            # For now, create dummy individuals with random lists
            for _ in range(self.max_size):
                genotype = [random.randint(0, 100) for _ in range(10)]
                ind = Individual(
                    id=self._generate_id(),
                    genotype=genotype,
                    phenotype=genotype,
                    fitness=0.0,
                    age=0,
                    metadata={"source": "random"}
                )
                if fitness_function:
                    ind.fitness = fitness_function(ind)
                self._individuals[ind.id] = ind
        
        return list(self._individuals.values())
    
    def select_parent(self) -> Individual:
        """
        Select a parent individual based on the configured selection method.
        
        Returns:
            Selected Individual.
        
        Raises:
            PopulationError: If population is empty or selection fails.
        """
        if not self._individuals:
            raise PopulationError("Cannot select from empty population")
        
        individuals = list(self._individuals.values())
        
        if self.selection_method == SelectionMethod.TOURNAMENT:
            candidates = random.sample(individuals, min(self.tournament_size, len(individuals)))
            return max(candidates, key=lambda x: x.fitness)
        
        elif self.selection_method == SelectionMethod.RANK:
            # Sort by fitness and select based on rank probability
            sorted_inds = sorted(individuals, key=lambda x: x.fitness, reverse=True)
            # Simple linear rank selection
            ranks = [len(sorted_inds) - i for i in range(len(sorted_inds))]
            total_rank = sum(ranks)
            probs = [r / total_rank for r in ranks]
            selected = random.choices(sorted_inds, weights=probs, k=1)[0]
            return selected
        
        elif self.selection_method == SelectionMethod.ELITE:
            # Return the best individual
            return max(individuals, key=lambda x: x.fitness)
        
        else:
            # Default: random selection
            return random.choice(individuals)
    
    def select_parents(self, count: int) -> List[Individual]:
        """Select multiple parents for reproduction."""
        return [self.select_parent() for _ in range(count)]
    
    def crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Any, Any]:
        """
        Perform crossover between two parents.
        
        Args:
            parent1: First parent.
            parent2: Second parent.
        
        Returns:
            Tuple of (child_genotype, child2_genotype).
        """
        g1 = parent1.genotype
        g2 = parent2.genotype
        
        if not isinstance(g1, list) or not isinstance(g2, list):
            # Fallback for non-list genotypes: swap entire genotypes
            return g2, g1
        
        if random.random() > self.crossover_rate:
            return g1, g2
        
        # Single-point crossover
        if len(g1) == 0 or len(g2) == 0:
            return g1, g2
        
        point = random.randint(1, max(len(g1), len(g2)) - 1)
        
        c1 = g1[:point] + g2[point:]
        c2 = g2[:point] + g1[point:]
        
        return c1, c2
    
    def mutate(self, genotype: Any) -> Any:
        """
        Apply mutation to a genotype.
        
        Args:
            genotype: The genotype to mutate.
        
        Returns:
            Mutated genotype.
        """
        if not isinstance(genotype, list):
            return genotype
        
        mutated = genotype.copy()
        for i in range(len(mutated)):
            if random.random() < self.mutation_rate:
                # Simple mutation: random value change
                mutated[i] = random.randint(0, 100)
        
        return mutated
    
    def create_offspring(
        self,
        parent1: Individual,
        parent2: Individual
    ) -> Individual:
        """
        Create a new offspring from two parents.
        
        Args:
            parent1: First parent.
            parent2: Second parent.
        
        Returns:
            New Individual.
        """
        c1_genotype, _ = self.crossover(parent1, parent2)
        c1_genotype = self.mutate(c1_genotype)
        
        child = Individual(
            id=self._generate_id(),
            genotype=c1_genotype,
            phenotype=c1_genotype,
            fitness=0.0,
            age=0,
            parent_ids=[parent1.id, parent2.id],
            metadata={"source": "crossover"}
        )
        
        return child
    
    def evaluate_fitness(
        self,
        individuals: List[Individual],
        fitness_function: Callable[[Individual], float]
    ) -> List[Individual]:
        """
        Evaluate fitness for a list of individuals.
        
        Args:
            individuals: List of individuals to evaluate.
            fitness_function: Function to compute fitness.
        
        Returns:
            List of individuals with updated fitness values.
        """
        for ind in individuals:
            ind.fitness = fitness_function(ind)
        return individuals
    
    def replace_population(
        self,
        new_individuals: List[Individual],
        fitness_function: Optional[Callable[[Individual], float]] = None
    ) -> List[Individual]:
        """
        Replace the current population with new individuals, preserving elites.
        
        Args:
            new_individuals: New individuals to add to the population.
            fitness_function: Optional function to evaluate fitness of new individuals.
        
        Returns:
            The updated population list.
        """
        if fitness_function:
            new_individuals = self.evaluate_fitness(new_individuals, fitness_function)
        
        # Get current elites
        current_inds = list(self._individuals.values())
        elites = sorted(current_inds, key=lambda x: x.fitness, reverse=True)[:self.elite_count]
        
        # Increment age for survivors
        for ind in elites:
            ind.age += 1
        
        # Combine elites and new individuals
        combined = elites + new_individuals
        
        # Sort by fitness and keep top max_size
        combined.sort(key=lambda x: x.fitness, reverse=True)
        top_inds = combined[:self.max_size]
        
        # Update population
        self._individuals.clear()
        for ind in top_inds:
            self._individuals[ind.id] = ind
        
        self.generation += 1
        
        # Manage memory
        self._check_memory_usage()
        
        return list(self._individuals.values())
    
    def _check_memory_usage(self) -> None:
        """Check current memory usage and trigger GC if necessary."""
        # Simple memory estimation (in MB)
        # In a real implementation, use psutil or tracemalloc for accuracy
        total_size = sum(sys.getsizeof(ind.genotype) + sys.getsizeof(ind.phenotype) 
                        for ind in self._individuals.values())
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb > self.memory_threshold_mb:
            log.warning(f"Population memory usage ({total_size_mb:.2f} MB) exceeds threshold ({self.memory_threshold_mb} MB). Triggering GC.")
            gc.collect()
    
    def get_stats(self) -> PopulationStats:
        """
        Calculate and return current population statistics.
        
        Returns:
            PopulationStats object.
        """
        if not self._individuals:
            return PopulationStats(
                size=0, avg_fitness=0.0, max_fitness=0.0, min_fitness=0.0,
                std_fitness=0.0, avg_age=0.0, diversity_score=0.0,
                generation=self.generation, memory_usage_mb=0.0
            )
        
        individuals = list(self._individuals.values())
        fitnesses = [ind.fitness for ind in individuals]
        ages = [ind.age for ind in individuals]
        
        avg_fit = sum(fitnesses) / len(fitnesses)
        max_fit = max(fitnesses)
        min_fit = min(fitnesses)
        std_fit = (sum((f - avg_fit) ** 2 for f in fitnesses) / len(fitnesses)) ** 0.5
        avg_age = sum(ages) / len(ages)
        
        # Simple diversity: count unique genotypes (approximation)
        unique_genotypes = len(set(tuple(g) if isinstance(g, list) else g for g in [ind.genotype for ind in individuals]))
        diversity = unique_genotypes / len(individuals)
        
        # Memory estimate
        total_size = sum(sys.getsizeof(ind.genotype) + sys.getsizeof(ind.phenotype) 
                        for ind in individuals)
        mem_mb = total_size / (1024 * 1024)
        
        return PopulationStats(
            size=len(individuals),
            avg_fitness=avg_fit,
            max_fitness=max_fit,
            min_fitness=min_fit,
            std_fitness=std_fit,
            avg_age=avg_age,
            diversity_score=diversity,
            generation=self.generation,
            memory_usage_mb=mem_mb
        )
    
    def get_best_individual(self) -> Optional[Individual]:
        """Return the individual with the highest fitness."""
        if not self._individuals:
            return None
        return max(self._individuals.values(), key=lambda x: x.fitness)
    
    def save_population(self, filepath: str) -> None:
        """
        Save the current population to a JSON file.
        
        Args:
            filepath: Path to save the population data.
        """
        data = {
            "generation": self.generation,
            "individuals": [ind.to_dict() for ind in self._individuals.values()],
            "stats": self.get_stats().to_dict()
        }
        
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    
    def load_population(self, filepath: str) -> None:
        """
        Load a population from a JSON file.
        
        Args:
            filepath: Path to the population data file.
        """
        with open(filepath, "r") as f:
            data = json.load(f)
        
        self.generation = data.get("generation", 0)
        self._individuals.clear()
        
        for ind_data in data["individuals"]:
            ind = Individual.from_dict(ind_data)
            self._individuals[ind.id] = ind
        
        # Reset ID counter to avoid collisions
        if self._individuals:
            self._id_counter = max(int(ind.id.split("_")[-1]) for ind in self._individuals.values() if "_" in ind.id)

def main():
    """
    Main entry point for testing population management.
    Demonstrates initialization, evolution, and statistics.
    """
    log.info("Starting Population Management Test")
    
    # Create a simple fitness function
    def simple_fitness(ind: Individual) -> float:
        if isinstance(ind.genotype, list):
            return sum(ind.genotype) / len(ind.genotype)
        return 0.0
    
    # Initialize population
    pop = Population(max_size=20, elite_count=2, selection_method=SelectionMethod.TOURNAMENT)
    pop.initialize(fitness_function=simple_fitness, seed=42)
    
    log.info(f"Initial population size: {len(pop._individuals)}")
    stats = pop.get_stats()
    log.info(f"Initial stats: {stats.to_dict()}")
    
    # Run a few generations
    for gen in range(5):
        parents = pop.select_parents(10)
        offspring = []
        for i in range(0, len(parents), 2):
            if i + 1 < len(parents):
                child = pop.create_offspring(parents[i], parents[i+1])
                offspring.append(child)
        
        if offspring:
            offspring = pop.evaluate_fitness(offspring, simple_fitness)
            pop.replace_population(offspring, simple_fitness)
        
        stats = pop.get_stats()
        log.info(f"Generation {gen + 1} stats: avg_fit={stats.avg_fitness:.4f}, max_fit={stats.max_fitness:.4f}, mem={stats.memory_usage_mb:.2f}MB")
    
    # Save and load
    test_path = "data/processed/test_population.json"
    pop.save_population(test_path)
    log.info(f"Population saved to {test_path}")
    
    new_pop = Population(max_size=20)
    new_pop.load_population(test_path)
    log.info(f"Population loaded. Size: {len(new_pop._individuals)}")
    
    best = new_pop.get_best_individual()
    if best:
        log.info(f"Best individual: {best}")
    
    log.info("Population Management Test Complete")

if __name__ == "__main__":
    main()
