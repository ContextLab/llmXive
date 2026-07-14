# Simulation module initialization
"""
Simulation engine for generating synthetic meta-analysis datasets.

This module exposes the core classes and functions for data generation,
including the simulation generator and related utilities.
"""

from .generator import (
    generate_synthetic_meta_analysis,
    create_replicate,
    validate_simulation_output,
    SimulationConfig,
    SimulationResult
)

__all__ = [
    "generate_synthetic_meta_analysis",
    "create_replicate",
    "validate_simulation_output",
    "SimulationConfig",
    "SimulationResult"
]

# Import logger if needed for module-level logging
try:
    from utils.logging import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback if utils not yet available during initial setup
    import logging
    logger = logging.getLogger(__name__)
