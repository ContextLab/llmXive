"""
Population management for the Bidirectional Evolutionary Search (BES).

This module handles the evolutionary population, ensuring memory usage stays
under a manageable threshold and providing selection mechanisms for the
evolutionary loop.
"""
import gc
import time
import json
import random
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

# Import from project API
from code.utils.seed import set_seed, get_seed
from code.utils.logger import log, setup_logging
from code.exceptions import BaseResearchException

# Configure logging for this module
logger = logging.getLogger(__name__)

class PopulationError(BaseResearchException):
    """Custom exception for population-related errors."""
    pass

class SelectionMethod(Enum):
    """Enumeration of selection methods for evolutionary steps."""
    ROULETTE = "roulette"
    TOURNAMENT = "tournament"
    RANK = "rank"
    ELITISM = "elitism"

@dataclass
class Individual:
    """Represents a single individual in the evolutionary population."""
    id: str
    genotype: Any  # Can be a list, dict, or custom object representing the solution
    fitness: float
    age: int = 0
    generation_created: int = 0
    parent_ids: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.parent_ids is None:
            self.parent_ids = []
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert individual to a dictionary for serialization."""
        return asdict(self)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Individual':
        """Create an Individual from a dictionary."""
        return cls(**data)

@dataclass
class PopulationStats:
    """Statistics about the current population state."""
    size: int
    avg_fitness: float
    min_fitness: float
    max_fitness: float
    std_fitness: float
    generation: int
    memory_usage_mb: float
    diversity_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to a dictionary."""
        return asdict(self)

class Population:
    """
    Manages the evolutionary population for BES.
    
    Ensures memory usage stays under a manageable threshold and provides
    selection mechanisms for the evolutionary loop.
    """
    
    def __init__(
        self,
        size: int,
        generation: int = 0,
        seed: Optional[int] = None,
        max_memory_mb: Optional[float] = None
    ):
        """
        Initialize a new population.
        
        Args:
            size: Maximum population size.
            generation: Current generation number.
            seed: Random seed for reproducibility.
            max_memory_mb: Optional maximum memory usage in MB. If exceeded,
                          garbage collection is triggered.
        """
        self.size = size
        self.generation = generation
        self.max_memory_mb = max_memory_mb
        self.individuals: List[Individual] = []
        self.history: List[Dict[str, Any]] = []
        
        if seed is not None:
            set_seed(seed)
            self.seed = seed
        else:
            self.seed = get_seed()
            
        random.seed(self.seed)
        logger.info(f"Initialized population with size {size}, seed {self.seed}")
        
        # Memory monitoring
        self._last_gc_generation = 0
        self._gc_threshold = 10  # Run GC every 10 generations if no explicit limit
        
    def add_individual(self, individual: Individual) -> None:
        """
        Add an individual to the population.
        
        Args:
            individual: The Individual to add.
            
        Raises:
            PopulationError: If population exceeds max size.
        """
        if len(self.individuals) >= self.size:
            raise PopulationError(
                f"Population size {len(self.individuals)} already at maximum {self.size}"
            )
        self.individuals.append(individual)
        logger.debug(f"Added individual {individual.id} to population")
        
    def initialize_random(
        self,
        generator_func,
        num_individuals: Optional[int] = None
    ) -> List[Individual]:
        """
        Initialize the population with random individuals.
        
        Args:
            generator_func: A callable that generates a random individual.
                            Should return an Individual or data to wrap in one.
            num_individuals: Number of individuals to generate. Defaults to self.size.
                            
        Returns:
            List of generated individuals.
        """
        count = num_individuals or self.size
        self.individuals = []
        
        for i in range(count):
            ind_data = generator_func()
            if isinstance(ind_data, Individual):
                individual = ind_data
            else:
                # Assume it's genotype data, wrap it
                individual = Individual(
                    id=f"init_{self.generation}_{i}",
                    genotype=ind_data,
                    fitness=0.0,
                    generation_created=self.generation
                )
            self.individuals.append(individual)
            
        logger.info(f"Initialized population with {len(self.individuals)} random individuals")
        return self.individuals
        
    def get_fitnesses(self) -> List[float]:
        """Get list of fitness values for all individuals."""
        return [ind.fitness for ind in self.individuals]
        
    def get_best_individual(self) -> Optional[Individual]:
        """Return the individual with the highest fitness."""
        if not self.individuals:
            return None
        return max(self.individuals, key=lambda ind: ind.fitness)
        
    def get_worst_individual(self) -> Optional[Individual]:
        """Return the individual with the lowest fitness."""
        if not self.individuals:
            return None
        return min(self.individuals, key=lambda ind: ind.fitness)
        
    def select_parent(
        self,
        method: SelectionMethod = SelectionMethod.TOURNAMENT,
        tournament_size: int = 3,
        elite_count: int = 0
    ) -> Individual:
        """
        Select a parent from the population using the specified method.
        
        Args:
            method: The selection method to use.
            tournament_size: Size of tournament for tournament selection.
            elite_count: Number of elite individuals to preserve (for elitism).
            
        Returns:
            Selected Individual.
            
        Raises:
            PopulationError: If population is empty or selection fails.
        """
        if not self.individuals:
            raise PopulationError("Cannot select parent from empty population")
            
        if method == SelectionMethod.ELITISM and elite_count > 0:
            # Sort by fitness descending and pick from top
            sorted_inds = sorted(self.individuals, key=lambda x: x.fitness, reverse=True)
            if elite_count <= len(sorted_inds):
                return sorted_inds[elite_count - 1]
            else:
                # Fall back to random if elite count is too high
                return random.choice(self.individuals)
                
        elif method == SelectionMethod.TOURNAMENT:
            if tournament_size > len(self.individuals):
                tournament_size = len(self.individuals)
            tournament = random.sample(self.individuals, tournament_size)
            return max(tournament, key=lambda ind: ind.fitness)
            
        elif method == SelectionMethod.ROULETTE:
            fitnesses = self.get_fitnesses()
            min_fit = min(fitnesses)
            # Shift to ensure non-negative values for probability
            shifted = [f - min_fit + 1e-6 for f in fitnesses]
            total = sum(shifted)
            if total == 0:
                return random.choice(self.individuals)
            
            # Calculate cumulative probabilities
            probs = [s / total for s in shifted]
            r = random.random()
            cumulative = 0.0
            for i, prob in enumerate(probs):
                cumulative += prob
                if r <= cumulative:
                    return self.individuals[i]
            return self.individuals[-1]
            
        elif method == SelectionMethod.RANK:
            # Sort by fitness
            sorted_inds = sorted(self.individuals, key=lambda ind: ind.fitness)
            n = len(sorted_inds)
            # Assign ranks (1 to n)
            ranks = list(range(1, n + 1))
            total_rank = sum(ranks)
            probs = [r / total_rank for r in ranks]
            
            r = random.random()
            cumulative = 0.0
            for i, prob in enumerate(probs):
                cumulative += prob
                if r <= cumulative:
                    return sorted_inds[i]
            return sorted_inds[-1]
            
        else:
            # Default to tournament
            return self.select_parent(SelectionMethod.TOURNAMENT, tournament_size)
            
    def crossover(
        self,
        parent1: Individual,
        parent2: Individual,
        crossover_rate: float = 0.8
    ) -> Tuple[Individual, Individual]:
        """
        Perform crossover between two parents.
        
        Args:
            parent1: First parent.
            parent2: Second parent.
            crossover_rate: Probability of crossover occurring.
            
        Returns:
            Tuple of two offspring individuals.
        """
        if random.random() > crossover_rate:
            # No crossover, return copies
            child1 = Individual(
                id=f"child_{self.generation}_{time.time()}_1",
                genotype=parent1.genotype,
                fitness=0.0,
                generation_created=self.generation + 1,
                parent_ids=[parent1.id, parent2.id]
            )
            child2 = Individual(
                id=f"child_{self.generation}_{time.time()}_2",
                genotype=parent2.genotype,
                fitness=0.0,
                generation_created=self.generation + 1,
                parent_ids=[parent1.id, parent2.id]
            )
            return child1, child2
            
        # Simple uniform crossover for lists
        if isinstance(parent1.genotype, list) and isinstance(parent2.genotype, list):
            if len(parent1.genotype) != len(parent2.genotype):
                # Fallback: swap entire genotypes
                child1 = Individual(
                    id=f"child_{self.generation}_{time.time()}_1",
                    genotype=parent2.genotype,
                    fitness=0.0,
                    generation_created=self.generation + 1,
                    parent_ids=[parent1.id, parent2.id]
                )
                child2 = Individual(
                    id=f"child_{self.generation}_{time.time()}_2",
                    genotype=parent1.genotype,
                    fitness=0.0,
                    generation_created=self.generation + 1,
                    parent_ids=[parent1.id, parent2.id]
                )
                return child1, child2
                
            child1_genotype = []
            child2_genotype = []
            for i in range(len(parent1.genotype)):
                if random.random() < 0.5:
                    child1_genotype.append(parent1.genotype[i])
                    child2_genotype.append(parent2.genotype[i])
                else:
                    child1_genotype.append(parent2.genotype[i])
                    child2_genotype.append(parent1.genotype[i])
                    
            child1 = Individual(
                id=f"child_{self.generation}_{time.time()}_1",
                genotype=child1_genotype,
                fitness=0.0,
                generation_created=self.generation + 1,
                parent_ids=[parent1.id, parent2.id]
            )
            child2 = Individual(
                id=f"child_{self.generation}_{time.time()}_2",
                genotype=child2_genotype,
                fitness=0.0,
                generation_created=self.generation + 1,
                parent_ids=[parent1.id, parent2.id]
            )
            return child1, child2
            
        # Default: return copies
        child1 = Individual(
            id=f"child_{self.generation}_{time.time()}_1",
            genotype=parent1.genotype,
            fitness=0.0,
            generation_created=self.generation + 1,
            parent_ids=[parent1.id, parent2.id]
        )
        child2 = Individual(
            id=f"child_{self.generation}_{time.time()}_2",
            genotype=parent2.genotype,
            fitness=0.0,
            generation_created=self.generation + 1,
            parent_ids=[parent1.id, parent2.id]
        )
        return child1, child2
        
    def mutate(
        self,
        individual: Individual,
        mutation_rate: float = 0.1
    ) -> Individual:
        """
        Apply mutation to an individual.
        
        Args:
            individual: The individual to mutate.
            mutation_rate: Probability of mutating each gene/element.
                           
        Returns:
            A new mutated individual.
        """
        if isinstance(individual.genotype, list):
            new_genotype = individual.genotype.copy()
            for i in range(len(new_genotype)):
                if random.random() < mutation_rate:
                    # Simple mutation: flip or randomize
                    if isinstance(new_genotype[i], bool):
                        new_genotype[i] = not new_genotype[i]
                    elif isinstance(new_genotype[i], (int, float)):
                        new_genotype[i] += random.gauss(0, 0.1)
                    else:
                        # For other types, just keep original (no-op mutation)
                        pass
                        
            return Individual(
                id=f"mutated_{time.time()}",
                genotype=new_genotype,
                fitness=individual.fitness,
                generation_created=individual.generation_created,
                parent_ids=individual.parent_ids.copy() if individual.parent_ids else []
            )
        else:
            # Non-list genotype: return copy with slight modification if possible
            return Individual(
                id=f"mutated_{time.time()}",
                genotype=individual.genotype,
                fitness=individual.fitness,
                generation_created=individual.generation_created,
                parent_ids=individual.parent_ids.copy() if individual.parent_ids else []
            )
                
    def evolve_generation(
        self,
        fitness_func,
        selection_method: SelectionMethod = SelectionMethod.TOURNAMENT,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        elite_count: int = 1
    ) -> List[Individual]:
        """
        Evolve the population to the next generation.
        
        Args:
            fitness_func: Function to evaluate fitness of individuals.
            selection_method: Method for selecting parents.
            crossover_rate: Probability of crossover.
            mutation_rate: Probability of mutation per gene.
            elite_count: Number of top individuals to preserve unchanged.
            
        Returns:
            List of individuals in the new generation.
        """
        start_time = time.time()
        
        # Evaluate fitness for current population if not already done
        for ind in self.individuals:
            if ind.fitness == 0.0 and ind.id.startswith("init_"):
                ind.fitness = fitness_func(ind)
                
        # Sort by fitness for elitism
        sorted_inds = sorted(self.individuals, key=lambda ind: ind.fitness, reverse=True)
        new_population = sorted_inds[:elite_count]
        
        # Generate rest of population
        while len(new_population) < self.size:
            parent1 = self.select_parent(selection_method, elite_count=elite_count)
            parent2 = self.select_parent(selection_method, elite_count=elite_count)
            
            child1, child2 = self.crossover(parent1, parent2, crossover_rate)
            child1 = self.mutate(child1, mutation_rate)
            child2 = self.mutate(child2, mutation_rate)
            
            # Evaluate fitness
            child1.fitness = fitness_func(child1)
            child2.fitness = fitness_func(child2)
            
            new_population.append(child1)
            if len(new_population) < self.size:
                new_population.append(child2)
                
        # Replace old population
        self.individuals = new_population
        self.generation += 1
        
        # Update age of all individuals
        for ind in self.individuals:
            ind.age += 1
            
        # Memory management
        self._check_memory()
        
        elapsed = time.time() - start_time
        logger.info(f"Evolved generation {self.generation} in {elapsed:.2f}s")
        
        return self.individuals
        
    def _check_memory(self) -> None:
        """Check memory usage and trigger GC if necessary."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)
            
            if self.max_memory_mb and mem_mb > self.max_memory_mb:
                logger.warning(f"Memory usage {mem_mb:.1f}MB exceeds limit {self.max_memory_mb}MB")
                gc.collect()
                self._last_gc_generation = self.generation
                
            elif self.generation - self._last_gc_generation >= self._gc_threshold:
                gc.collect()
                self._last_gc_generation = self.generation
                
        except ImportError:
            # psutil not available, skip memory check
            pass
            
    def get_stats(self) -> PopulationStats:
        """Calculate and return current population statistics."""
        if not self.individuals:
            return PopulationStats(
                size=0,
                avg_fitness=0.0,
                min_fitness=0.0,
                max_fitness=0.0,
                std_fitness=0.0,
                generation=self.generation,
                memory_usage_mb=0.0
            )
            
        fitnesses = self.get_fitnesses()
        avg_fit = sum(fitnesses) / len(fitnesses)
        min_fit = min(fitnesses)
        max_fit = max(fitnesses)
        variance = sum((f - avg_fit) ** 2 for f in fitnesses) / len(fitnesses)
        std_fit = variance ** 0.5
        
        # Estimate memory usage
        mem_mb = 0.0
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_mb = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            pass
            
        # Calculate diversity (simple: count unique genotypes)
        unique_genotypes = len(set(str(ind.genotype) for ind in self.individuals))
        diversity = unique_genotypes / len(self.individuals) if self.individuals else 0.0
        
        return PopulationStats(
            size=len(self.individuals),
            avg_fitness=avg_fit,
            min_fitness=min_fit,
            max_fitness=max_fit,
            std_fitness=std_fit,
            generation=self.generation,
            memory_usage_mb=mem_mb,
            diversity_score=diversity
        )
        
    def to_json(self) -> str:
        """Serialize population to JSON string."""
        data = {
            "generation": self.generation,
            "size": self.size,
            "seed": self.seed,
            "individuals": [ind.to_dict() for ind in self.individuals]
        }
        return json.dumps(data, indent=2)
        
    @classmethod
    def from_json(cls, json_str: str) -> 'Population':
        """Deserialize population from JSON string."""
        data = json.loads(json_str)
        pop = cls(
            size=data["size"],
            generation=data["generation"],
            seed=data.get("seed")
        )
        pop.individuals = [Individual.from_dict(ind) for ind in data["individuals"]]
        return pop
        
    def save_to_file(self, filepath: str) -> None:
        """Save population to a JSON file."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.to_json())
        logger.info(f"Saved population to {filepath}")
        
    @classmethod
    def load_from_file(cls, filepath: str) -> 'Population':
        """Load population from a JSON file."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Population file not found: {filepath}")
            
        with open(path, 'r') as f:
            json_str = f.read()
        return cls.from_json(json_str)

def main():
    """Main entry point for testing/running population module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Population management for BES")
    parser.add_argument("--size", type=int, default=10, help="Population size")
    parser.add_argument("--generations", type=int, default=5, help="Number of generations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/processed/population_test.json", 
                      help="Output file path")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    # Define a simple fitness function for testing
    def simple_fitness(ind):
        # Sum of genotype elements (assuming numeric list)
        if isinstance(ind.genotype, list):
            return sum(float(x) for x in ind.genotype if isinstance(x, (int, float)))
        return 0.0
        
    # Create population
    pop = Population(size=args.size, seed=args.seed)
    
    # Initialize with random data
    def random_genotype():
        return [random.random() for _ in range(10)]
        
    pop.initialize_random(random_genotype)
    
    # Evolve
    for gen in range(args.generations):
        pop.evolve_generation(
            fitness_func=simple_fitness,
            selection_method=SelectionMethod.TOURNAMENT,
            elite_count=1
        )
        stats = pop.get_stats()
        logger.info(f"Generation {pop.generation}: avg={stats.avg_fitness:.4f}, "
                   f"max={stats.max_fitness:.4f}, diversity={stats.diversity_score:.4f}")
                   
    # Save result
    pop.save_to_file(args.output)
    print(f"Population saved to {args.output}")
    
    # Print final stats
    final_stats = pop.get_stats()
    print(json.dumps(final_stats.to_dict(), indent=2))

if __name__ == "__main__":
    main()