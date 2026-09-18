"""
Configuration parameters for the MD diffusion predictive power investigation.

Defines solvents, timescales, force fields, and analysis thresholds.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
import os

class Solvent(Enum):
    """Supported solvents for simulation and analysis."""
    WATER = "water"
    ETHANOL = "ethanol"
    ACETONE = "acetone"

@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for MD simulations."""
    force_field: str = "MARTINI"
    temperature: float = 300.0  # Kelvin
    pressure: float = 1.0  # bar
    time_step: float = 0.02  # ns
    density_tolerance: float = 0.01  # ±1%
    density_window: float = 0.2  # 200ps
    timeout_seconds: int = 3600
    scaling_factors: Dict[str, float] = field(default_factory=lambda: {
        "water": 1.0,
        "ethanol": 1.2,
        "acetone": 0.9
    })

@dataclass(frozen=True)
class AnalysisConfig:
    """Configuration for analysis and reporting."""
    r_squared_threshold: float = 0.95
    sensitivity_start_times: List[float] = field(default_factory=lambda: [0.1, 0.2, 0.3])
    bootstrap_target_iterations: int = 1000
    bootstrap_min_iterations: int = 100
    bootstrap_time_limit_hours: float = 5.5
    variance_threshold_percent: float = 5.0
    nist_refs_path: str = os.path.join("data", "raw", "nist_refs.json")
    manifest_path: str = os.path.join("data", "raw", "manifest.json")

# Global configuration instances
SIMULATION_CONFIG = SimulationConfig()
ANALYSIS_CONFIG = AnalysisConfig()

# Timescales in nanoseconds
TIMESCALES: List[float] = [1.0, 5.0, 10.0]

# Output paths
OUTPUT_DIR = "data/processed"
FIGURES_DIR = "figures"
LOGS_DIR = "logs"
