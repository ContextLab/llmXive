"""
Configuration parameters for the MD diffusion predictive power investigation.

This module defines all static configuration used across the pipeline,
including solvents, simulation timescales, force field settings, and
analysis thresholds.

Key Principles:
- R² threshold set to 0.95 per Constitution Principle VI (T008a tracks spec update).
- Scaling factors are solvent-specific multipliers for MARTINI diffusion.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum


class Solvent(str, Enum):
    WATER = "water"
    ETHANOL = "ethanol"
    ACETONE = "acetone"


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for a single simulation run."""
    solvent: Solvent
    duration_ns: float
    force_field: str = "MARTINI"
    # NPT equilibration parameters
    npt_temp_k: float = 300.0
    npt_pressure_bar: float = 1.0
    npt_duration_ps: float = 200.0
    # Production parameters
    prod_dt_fs: int = 20
    prod_freq_xtc: int = 100
    prod_freq_edr: int = 1000


@dataclass(frozen=True)
class AnalysisConfig:
    """Configuration for post-simulation analysis."""
    # Linearity threshold for MSD regression (R² >= threshold)
    # Set to 0.95 per Constitution Principle VI. T008a tracks spec alignment.
    msd_r2_threshold: float = 0.95
    # Solvent-specific scaling factors for MARTINI diffusion coefficients
    # (MARTINI typically overestimates diffusion, so factors < 1.0)
    scaling_factors: Dict[Solvent, float]
    # Bootstrap configuration
    bootstrap_n_iterations: int = 1000
    bootstrap_wall_clock_limit_seconds: float = 5.5 * 3600  # 5.5 hours
    bootstrap_fallback_iterations: int = 100
    # Variance threshold for sensitivity analysis
    sensitivity_variance_threshold: float = 0.05  # 5%


# Define all solvents to be simulated
SOLVENTS: List[Solvent] = [
    Solvent.WATER,
    Solvent.ETHANOL,
    Solvent.ACETONE,
]

# Define simulation timescales (in nanoseconds)
TIMESCALES_NS: List[float] = [1.0, 5.0, 10.0]

# Default force field
FORCE_FIELD: str = "MARTINI"

# Analysis configuration with solvent-specific scaling factors
# Source: Literature values for MARTINI water/ethanol/acetone diffusion correction
ANALYSIS_CONFIG = AnalysisConfig(
    msd_r2_threshold=0.95,  # Per Constitution Principle VI
    scaling_factors={
        Solvent.WATER: 0.5,      # Approximate correction for MARTINI water
        Solvent.ETHANOL: 0.6,    # Approximate correction for MARTINI ethanol
        Solvent.ACETONE: 0.55,   # Approximate correction for MARTINI acetone
    },
    bootstrap_n_iterations=1000,
    bootstrap_wall_clock_limit_seconds=5.5 * 3600,
    bootstrap_fallback_iterations=100,
    sensitivity_variance_threshold=0.05,
)

# NIST reference file path
NIST_REFS_PATH = "data/raw/nist_refs.json"

# Output paths
OUTPUT_DIR = "data/processed"
FIGURES_DIR = "figures"

# Log file path
LOG_FILE = "data/pipeline.log"