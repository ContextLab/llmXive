"""
BES (Bidirectional Evolutionary Search) module.

This module contains the core logic for the evolutionary search process,
including forward steps (LLM), backward steps (symbolic), population management,
and result aggregation.
"""

from .config import BESConfig, get_default_config
from .population import Population, Individual, SelectionMethod
from .forward_step import ForwardStep
from .backward_step import BackwardStep
from .evolutionary_loop import EvolutionaryLoop
from .result_aggregator import AggregatedResult, aggregate_results

__all__ = [
    'BESConfig',
    'get_default_config',
    'Population',
    'Individual',
    'SelectionMethod',
    'ForwardStep',
    'BackwardStep',
    'EvolutionaryLoop',
    'AggregatedResult',
    'aggregate_results'
]
