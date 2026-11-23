"""
Termination Condition Module for BES (Bidirectional Evolutionary Search)

Implements logic to stop the evolutionary loop based on:
1. Maximum generations reached
2. Convergence (no improvement in best fitness for N generations)
3. Early stopping based on target fitness threshold

This module integrates with the evolutionary loop (T025) to provide
a robust stopping mechanism that logs the specific reason for termination.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from bes.population import Individual, PopulationStats
from bes.config import BESConfig

logger = logging.getLogger(__name__)

@dataclass
class TerminationResult:
    """Result of a termination condition check."""
    should_stop: bool
    reason: str
    generation: int
    best_fitness: float
    stats: Optional[PopulationStats] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for logging."""
        return {
            "should_stop": self.should_stop,
            "reason": self.reason,
            "generation": self.generation,
            "best_fitness": self.best_fitness,
            "timestamp": self.timestamp,
            "stats": self.stats.to_dict() if self.stats else None
        }

class TerminationCondition:
    """
    Composite termination condition manager.

    Evaluates multiple stopping criteria and returns the first one triggered.
    Supports:
    - Max generations
    - Convergence (stagnation)
    - Target fitness threshold
    - Maximum runtime (optional)
    """

    def __init__(self, config: BESConfig):
        self.config = config
        self.max_generations = config.max_generations
        self.convergence_window = config.convergence_window
        self.target_fitness = config.target_fitness
        self.max_runtime = config.max_runtime_seconds
        self.start_time: Optional[float] = None
        self.history: List[float] = []  # Best fitness history
        self.last_improvement_generation = 0
        self.best_fitness_ever: float = -float('inf')

    def initialize(self, generation: int = 0):
        """Initialize timing and history tracking."""
        self.start_time = time.time()
        self.history = []
        self.last_improvement_generation = generation
        self.best_fitness_ever = -float('inf')
        logger.info(f"TerminationCondition initialized at generation {generation}")

    def check(self, generation: int, population_stats: PopulationStats) -> TerminationResult:
        """
        Check all termination conditions.

        Args:
            generation: Current generation number
            population_stats: Statistics from the current population

        Returns:
            TerminationResult with stop flag and reason
        """
        # Initialize on first check if not done
        if self.start_time is None:
            self.initialize(generation)

        current_best = population_stats.best_fitness
        self.history.append(current_best)

        # Update best ever
        if current_best > self.best_fitness_ever:
            self.best_fitness_ever = current_best
            self.last_improvement_generation = generation

        # 1. Check Max Generations
        if generation >= self.max_generations:
            logger.info(
                f"Termination triggered: Max generations reached "
                f"({generation}/{self.max_generations})"
            )
            return TerminationResult(
                should_stop=True,
                reason=f"max_generations_reached:{generation}/{self.max_generations}",
                generation=generation,
                best_fitness=current_best,
                stats=population_stats
            )

        # 2. Check Convergence (Stagnation)
        if len(self.history) >= self.convergence_window:
            recent_history = self.history[-self.convergence_window:]
            # Check if no significant improvement in the window
            # Improvement threshold: 1e-6 to avoid floating point noise
            improvement = max(recent_history) - min(recent_history)
            if improvement < 1e-6:
                generations_without_improvement = generation - self.last_improvement_generation
                logger.info(
                    f"Termination triggered: Convergence detected "
                    f"(no improvement in {self.convergence_window} generations, "
                    f"last improvement at gen {self.last_improvement_generation})"
                )
                return TerminationResult(
                    should_stop=True,
                    reason=f"convergence:{self.convergence_window}_generations_stagnation",
                    generation=generation,
                    best_fitness=current_best,
                    stats=population_stats
                )

        # 3. Check Target Fitness
        if self.target_fitness is not None:
            if current_best >= self.target_fitness:
                logger.info(
                    f"Termination triggered: Target fitness reached "
                    f"({current_best:.4f} >= {self.target_fitness:.4f})"
                )
                return TerminationResult(
                    should_stop=True,
                    reason=f"target_fitness_reached:{current_best:.4f}",
                    generation=generation,
                    best_fitness=current_best,
                    stats=population_stats
                )

        # 4. Check Max Runtime
        if self.max_runtime is not None and self.start_time is not None:
            elapsed = time.time() - self.start_time
            if elapsed >= self.max_runtime:
                logger.info(
                    f"Termination triggered: Max runtime exceeded "
                    f"({elapsed:.2f}s >= {self.max_runtime}s)"
                )
                return TerminationResult(
                    should_stop=True,
                    reason=f"max_runtime_exceeded:{elapsed:.2f}s",
                    generation=generation,
                    best_fitness=current_best,
                    stats=population_stats
                )

        # No termination condition met
        return TerminationResult(
            should_stop=False,
            reason="continuing",
            generation=generation,
            best_fitness=current_best,
            stats=population_stats
        )

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the termination state."""
        return {
            "max_generations": self.max_generations,
            "convergence_window": self.convergence_window,
            "target_fitness": self.target_fitness,
            "max_runtime_seconds": self.max_runtime,
            "generations_run": len(self.history),
            "best_fitness_ever": self.best_fitness_ever,
            "last_improvement_generation": self.last_improvement_generation
        }

def main():
    """
    Standalone test for TerminationCondition.

    Simulates a few generations and verifies termination logic.
    """
    import sys
    from bes.config import get_default_config

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Load config
    config = get_default_config()
    config.max_generations = 10
    config.convergence_window = 3
    config.target_fitness = None
    config.max_runtime_seconds = None

    # Create termination condition
    term_cond = TerminationCondition(config)
    term_cond.initialize(0)

    # Simulate population stats
    class MockStats:
        def __init__(self, fitness):
            self.best_fitness = fitness
            self.avg_fitness = fitness * 0.8
            self.worst_fitness = fitness * 0.5
            self.diversity = 0.5

        def to_dict(self):
            return {
                "best_fitness": self.best_fitness,
                "avg_fitness": self.avg_fitness,
                "worst_fitness": self.worst_fitness,
                "diversity": self.diversity
            }

    # Test 1: Normal progression
    print("Test 1: Normal progression (no termination)")
    for gen in range(1, 5):
        stats = MockStats(0.5 + gen * 0.1)  # Increasing fitness
        result = term_cond.check(gen, stats)
        print(f"  Gen {gen}: should_stop={result.should_stop}, reason={result.reason}")
        assert not result.should_stop, "Should not stop during normal progression"

    # Test 2: Max generations
    print("\nTest 2: Max generations reached")
    stats = MockStats(0.9)
    result = term_cond.check(10, stats)
    print(f"  Gen 10: should_stop={result.should_stop}, reason={result.reason}")
    assert result.should_stop, "Should stop at max generations"
    assert "max_generations_reached" in result.reason

    # Test 3: Convergence
    print("\nTest 3: Convergence (stagnation)")
    config2 = get_default_config()
    config2.max_generations = 100
    config2.convergence_window = 3
    term_cond2 = TerminationCondition(config2)
    term_cond2.initialize(0)

    # Simulate stagnation
    for gen in range(1, 5):
        stats = MockStats(0.5)  # Constant fitness
        result = term_cond2.check(gen, stats)
        print(f"  Gen {gen}: should_stop={result.should_stop}, reason={result.reason}")

    # Should stop at gen 3 (window size)
    assert result.should_stop, "Should stop due to convergence"
    assert "convergence" in result.reason

    # Test 4: Target fitness
    print("\nTest 4: Target fitness reached")
    config3 = get_default_config()
    config3.max_generations = 100
    config3.convergence_window = 10
    config3.target_fitness = 0.95
    term_cond3 = TerminationCondition(config3)
    term_cond3.initialize(0)

    stats = MockStats(0.96)
    result = term_cond3.check(5, stats)
    print(f"  Gen 5: should_stop={result.should_stop}, reason={result.reason}")
    assert result.should_stop, "Should stop at target fitness"
    assert "target_fitness_reached" in result.reason

    print("\nAll tests passed!")

if __name__ == "__main__":
    main()
