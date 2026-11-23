"""
Data Model for Sensitivity Analysis Reports.

Defines the schema for storing results from the sensitivity sweep
performed in code/analysis/sensitivity.py.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json


@dataclass
class SensitivityResult:
    """Single data point from the sensitivity sweep."""
    start_fraction: float
    diffusion_coefficient_cm2_s: float
    r_squared: float
    start_time_ps: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_fraction": self.start_fraction,
            "diffusion_coefficient_cm2_s": self.diffusion_coefficient_cm2_s,
            "r_squared": self.r_squared,
            "start_time_ps": self.start_time_ps
        }


@dataclass
class SensitivityReport:
    """
    Aggregated report for a single solvent/timescale sensitivity analysis.
    
    Attributes:
        solvent: Name of the solvent analyzed.
        timescale_ns: Total simulation duration in nanoseconds.
        results: List of SensitivityResult objects for each sweep point.
        mean_diffusion_coefficient: Mean D across all valid sweep points.
        std_diffusion_coefficient: Standard deviation of D.
        relative_variance: std / mean (as a fraction).
        variance_threshold: The threshold used (default 0.05).
        variance_flag: True if relative_variance > threshold.
        sweep_fractions: The list of fractions used in the sweep.
        timestamp: ISO timestamp of generation.
    """
    solvent: str
    timescale_ns: float
    results: List[SensitivityResult]
    mean_diffusion_coefficient: float
    std_diffusion_coefficient: float
    relative_variance: float
    variance_threshold: float
    variance_flag: bool
    sweep_fractions: List[float]
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solvent": self.solvent,
            "timescale_ns": self.timescale_ns,
            "results": [r.to_dict() for r in self.results],
            "mean_diffusion_coefficient_cm2_s": self.mean_diffusion_coefficient,
            "std_diffusion_coefficient_cm2_s": self.std_diffusion_coefficient,
            "relative_variance": self.relative_variance,
            "variance_threshold": self.variance_threshold,
            "variance_flag": self.variance_flag,
            "sweep_fractions": self.sweep_fractions,
            "timestamp": self.timestamp
        }

    def save_json(self, path: str) -> None:
        """Save the report to a JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)