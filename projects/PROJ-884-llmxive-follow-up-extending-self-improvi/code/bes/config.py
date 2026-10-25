"""
Configuration module for the Bidirectional Evolutionary Search (BES) framework.

Provides a simple dataclass ``BESConfig`` with sensible defaults and a helper
``get_default_config`` that returns a ready‑to‑use configuration instance.
The function is required by ``code.bes.__init__`` which imports it at import
time; adding it here resolves the import error that prevented the pilot
runner from being executed.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class SelectionMethod(Enum):
    """Enumeration of supported parent‑selection strategies."""
    ROULETTE = "roulette"
    TOURNAMENT = "tournament"
    RANK = "rank"
    ELITISM = "elitism"

@dataclass
class BESConfig:
    """
    Minimal configuration container for the BES pipeline.

    Only a subset of fields is required for the pilot run; additional
    parameters can be added later without breaking existing code.
    """
    population_size: int = 30
    generations: int = 10
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_rate: float = 0.1
    selection_method: SelectionMethod = SelectionMethod.ROULETTE
    tournament_size: int = 3
    seed: int = 42
    device: str = "cpu"
    # Placeholder for TDP; the real calibrated value is written by a later task.
    tdp_watts: float = 65.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize the configuration to a plain dictionary."""
        return {
            "population_size": self.population_size,
            "generations": self.generations,
            "mutation_rate": self.mutation_rate,
            "crossover_rate": self.crossover_rate,
            "elite_rate": self.elite_rate,
            "selection_method": self.selection_method.value,
            "tournament_size": self.tournament_size,
            "seed": self.seed,
            "device": self.device,
            "tdp_watts": self.tdp_watts,
        }

def get_default_config() -> BESConfig:
    """
    Return a default ``BESConfig`` instance.

    This helper satisfies the import performed in ``code.bes.__init__`` and
    provides a single source of truth for default values used throughout
    the pilot implementation.
    """
    return BESConfig()
