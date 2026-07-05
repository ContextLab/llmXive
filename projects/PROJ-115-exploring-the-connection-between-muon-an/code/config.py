"""
Project Configuration and Global Parameters.
"""
from dataclasses import dataclass
from typing import Tuple

@dataclass
class GridParams:
    """
    Defines the search space for the parameter scan.
    Used by the AMR strategy and the main scan pipeline.
    """
    m_chi_min: float = 1.0       # MeV
    m_chi_max: float = 1000.0    # MeV
    m_V_min: float = 1.0         # MeV
    m_V_max: float = 1000.0      # MeV
    g_min: float = 1e-5
    g_max: float = 1e-1
    
    # AMR Specifics
    amr_max_depth: int = 5
    amr_tolerance: float = 0.05
    amr_refinement_threshold: float = 0.1
    amr_initial_resolution: int = 15

    def get_ranges(self) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        """Returns the ranges as tuples for the generator."""
        return (
            (self.m_chi_min, self.m_chi_max),
            (self.m_V_min, self.m_V_max),
            (self.g_min, self.g_max)
        )

# Global configuration instance
config = GridParams()
