"""
Configuration parameters for the MD diffusion study.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum
import os
from pathlib import Path


class Solvent(Enum):
    """Supported solvents for the study."""
    WATER = "water"
    ETHANOL = "ethanol"
    ACETONE = "acetone"


# Base directories relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INTERIM_DIR = DATA_DIR / "interim"
CODE_DIR = PROJECT_ROOT / "code"
LOGS_DIR = PROJECT_ROOT / "logs"

# NIST References path
NIST_REFS_PATH = RAW_DIR / "nist_refs.json"
MANIFEST_PATH = RAW_DIR / "manifest.json"

# R^2 threshold for linearity validation (updated per Spec Kickback T036)
R2_THRESHOLD = 0.95

# Scaling factors derived from literature review (Spec T005)
SCALING_FACTORS = {
    "water": 1.23,
    "ethanol": 0.85,
    "acetone": 1.15
}

@dataclass(frozen=True)
class SimulationConfig:
    """Configuration for MD simulations."""
    force_field: str = "MARTINI"
    time_step: float = 20.0  # fs
    temperature: float = 298.15  # K
    pressure: float = 1.0  # bar
    density_tolerance: float = 0.01  # 1%
    equilibration_time: float = 200.0  # ps
    timeout: float = 3600.0  # seconds (1 hour)
    # Timescales to simulate (in ns)
    timescales: Tuple[float, ...] = field(default_factory=lambda: (1.0, 5.0, 10.0))

@dataclass(frozen=True)
class AnalysisConfig:
    """Configuration for data analysis."""
    r2_threshold: float = 0.95
    bootstrap_iterations: int = 1000
    bootstrap_timeout: float = 5.5 * 3600  # 5.5 hours in seconds
    bootstrap_fallback: int = 100
    sensitivity_start_times: Tuple[float, ...] = field(default_factory=lambda: (0.1, 0.2, 0.3))
    variance_threshold: float = 0.05  # 5%

# Global instances
DEFAULT_SIMULATION_CONFIG = SimulationConfig()
DEFAULT_ANALYSIS_CONFIG = AnalysisConfig()
