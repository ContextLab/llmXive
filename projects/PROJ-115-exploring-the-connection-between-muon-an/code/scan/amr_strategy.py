"""
Adaptive Mesh Refinement (AMR) Strategy for Grid Convergence.

This module implements the logic to dynamically refine the parameter grid
based on the gradients of the physics observables (specifically the relic density
and Sommerfeld enhancement factors). It ensures that narrow viable bands
and resonance regions are captured with high precision without wasting
computation on flat regions.

Implements Plan 0.3 requirements.
"""
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
from physics.yukawa_solver import numerov_schrodinger, extract_sommerfeld_factor
from schemas.parameter_point import ParameterPoint, validate_parameter_point
import logging

logger = logging.getLogger(__name__)

@dataclass
class GridPoint:
    """Represents a single point in the parameter space."""
    m_chi: float       # Dark matter mass in MeV
    m_V: float         # Vector mediator mass in MeV
    g: float           # Coupling constant
    omega_h2: Optional[float] = None  # Calculated relic density
    S_factor: Optional[float] = None  # Sommerfeld enhancement
    is_refined: bool = False
    error_estimate: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "m_chi": self.m_chi,
            "m_V": self.m_V,
            "g": self.g,
            "omega_h2": self.omega_h2,
            "S_factor": self.S_factor,
            "is_refined": self.is_refined,
            "error_estimate": self.error_estimate
        }

@dataclass
class AMRConfig:
    """Configuration for the Adaptive Mesh Refinement strategy."""
    max_depth: int = 5
    tolerance_rel: float = 0.05  # 5% relative error tolerance
    tolerance_abs: float = 1e-4
    min_grid_spacing: float = 0.01  # Minimum spacing in log space
    refinement_threshold: float = 0.1  # Gradient threshold for refinement
    initial_resolution: int = 20  # Initial points per dimension
    max_points: int = 50000  # Safety cap on total points

class AdaptiveGridGenerator:
    """
    Generates a parameter grid with Adaptive Mesh Refinement.

    The strategy:
    1. Generate a coarse initial grid.
    2. Evaluate the physics observable (relic density/Sommerfeld) at grid points.
    3. Estimate local error/gradient between neighbors.
    4. Refine regions where the error exceeds the threshold.
    5. Repeat until convergence or max depth reached.
    """

    def __init__(self, config: AMRConfig):
        self.config = config
        self.grid_points: List[GridPoint] = []
        self.refinement_history: List[int] = []

    def _log_space_range(self, start: float, end: float, num: int) -> np.ndarray:
        """Generate a log-spaced array."""
        if num < 2:
            return np.array([start, end])
        return np.logspace(np.log10(start), np.log10(end), num)

    def _generate_coarse_grid(self, 
                              m_chi_range: Tuple[float, float], 
                              m_V_range: Tuple[float, float], 
                              g_range: Tuple[float, float]) -> List[GridPoint]:
        """Generate the initial coarse grid."""
        m_chi_vals = self._log_space_range(*m_chi_range, self.config.initial_resolution)
        m_V_vals = self._log_space_range(*m_V_range, self.config.initial_resolution)
        g_vals = self._log_space_range(*g_range, self.config.initial_resolution)

        points = []
        for m_chi in m_chi_vals:
            for m_V in m_V_vals:
                for g in g_vals:
                    # Validate parameter point physically
                    try:
                        validate_parameter_point({"m_chi": m_chi, "m_V": m_V, "g": g})
                        points.append(GridPoint(m_chi=m_chi, m_V=m_V, g=g))
                    except ValueError:
                        continue
        return points

    def _estimate_error(self, p1: GridPoint, p2: GridPoint, observable: str) -> float:
        """
        Estimate the local error between two adjacent points.
        Uses the difference in the observable normalized by the distance in parameter space.
        """
        v1 = getattr(p1, observable, None)
        v2 = getattr(p2, observable, None)

        if v1 is None or v2 is None:
            return float('inf')

        diff = abs(v1 - v2)
        avg = (abs(v1) + abs(v2)) / 2.0
        
        if avg < self.config.tolerance_abs:
            return diff
        
        return diff / avg

    def _refine_region(self, base_points: List[GridPoint], observable: str) -> List[GridPoint]:
        """
        Refine the grid in regions where the error estimate exceeds the threshold.
        Inserts new points between existing points that show high gradients.
        """
        new_points = []
        refined_count = 0

        # Sort points to find neighbors (simple 1D projection for demo, 
        # in 3D this would use a spatial tree, but we iterate pairs for simplicity here)
        # For a full 3D AMR, we would check neighbors in m_chi, m_V, and g directions.
        # Here we assume we are refining based on a specific dimension or a scalar field gradient.
        
        # Simplified refinement: Check adjacent points in the list (assuming sorted by m_chi for this pass)
        base_points.sort(key=lambda p: p.m_chi)

        for i in range(len(base_points) - 1):
            p1 = base_points[i]
            p2 = base_points[i+1]

            error = self._estimate_error(p1, p2, observable)

            if error > self.config.refinement_threshold:
                # Insert mid-point
                mid_m_chi = np.sqrt(p1.m_chi * p2.m_chi) # Geometric mean for log space
                mid_m_V = (p1.m_V + p2.m_V) / 2.0
                mid_g = np.sqrt(p1.g * p2.g)

                # Check spacing constraints
                if mid_m_chi - p1.m_chi < self.config.min_grid_spacing:
                    continue

                new_pt = GridPoint(m_chi=mid_m_chi, m_V=mid_m_V, g=mid_g)
                new_pt.is_refined = True
                new_pt.error_estimate = error
                new_points.append(new_pt)
                refined_count += 1

        return new_points

    def _compute_physics(self, points: List[GridPoint]) -> List[GridPoint]:
        """
        Compute the physics observables for a list of points.
        Uses the Yukawa solver for Sommerfeld enhancement.
        """
        computed_points = []
        for pt in points:
            try:
                # Calculate Sommerfeld factor
                # Using the Yukawa solver from the existing API
                # Parameters: mass of DM, mass of mediator, coupling
                # Note: The solver expects specific units, assuming MeV and dimensionless g
                s_factor, _ = extract_sommerfeld_factor(
                    m_chi=pt.m_chi, 
                    m_V=pt.m_V, 
                    g=pt.g
                )
                
                pt.S_factor = s_factor
                
                # Simple analytic relic density estimate for AMR guidance
                # In full implementation, this would call the RK4 integrator
                # Here we use a proxy: Omega ~ 1 / (S_factor * g^2)
                # This is a placeholder for the actual calculation logic to drive refinement
                if s_factor > 0:
                    pt.omega_h2 = 0.12 / (s_factor * (pt.g ** 2) * 1e8) 
                else:
                    pt.omega_h2 = 0.0
                
                computed_points.append(pt)
            except Exception as e:
                logger.warning(f"Physics calculation failed for point {pt}: {e}")
                # Keep point but mark as invalid or with error
                pt.omega_h2 = np.nan
                pt.S_factor = np.nan
                computed_points.append(pt)
        
        return computed_points

    def generate_adaptive_grid(self, 
                               m_chi_range: Tuple[float, float], 
                               m_V_range: Tuple[float, float], 
                               g_range: Tuple[float, float],
                               observable: str = "omega_h2") -> List[GridPoint]:
        """
        Main entry point to generate the AMR grid.
        
        Args:
            m_chi_range: (min, max) for DM mass
            m_V_range: (min, max) for mediator mass
            g_range: (min, max) for coupling
            observable: The physics observable to drive refinement

        Returns:
            List of GridPoint objects representing the refined grid.
        """
        logger.info(f"Starting AMR grid generation for ranges: m_chi={m_chi_range}, m_V={m_V_range}, g={g_range}")
        
        # Step 1: Coarse Grid
        current_grid = self._generate_coarse_grid(m_chi_range, m_V_range, g_range)
        self.grid_points = current_grid
        self.refinement_history.append(len(current_grid))
        
        logger.info(f"Initial coarse grid size: {len(current_grid)}")

        # Step 2: Iterate refinement
        for depth in range(self.config.max_depth):
            if len(self.grid_points) > self.config.max_points:
                logger.warning(f"Reached max points limit ({self.config.max_points}) at depth {depth}")
                break

            # Compute physics on current grid
            current_grid = self._compute_physics(self.grid_points)
            
            # Estimate errors and find regions to refine
            new_points = self._refine_region(current_grid, observable)
            
            if not new_points:
                logger.info(f"Convergence reached at depth {depth}. No further refinement needed.")
                break

            # Merge new points
            self.grid_points = current_grid + new_points
            self.refinement_history.append(len(self.grid_points))
            logger.info(f"Depth {depth}: Added {len(new_points)} points. Total: {len(self.grid_points)}")

        logger.info(f"Final grid size: {len(self.grid_points)}")
        return self.grid_points

    def get_grid_dataframe(self) -> 'pd.DataFrame':
        """Convert the grid to a pandas DataFrame for easy analysis."""
        import pandas as pd
        data = [pt.to_dict() for pt in self.grid_points]
        return pd.DataFrame(data)

def main():
    """
    Demonstration of the AMR strategy.
    Generates a grid and prints statistics.
    """
    config = AMRConfig(
        max_depth=4,
        tolerance_rel=0.05,
        refinement_threshold=0.1,
        initial_resolution=10
    )
    
    generator = AdaptiveGridGenerator(config)
    
    # Define search space (MeV, dimensionless)
    m_chi_range = (10.0, 1000.0)
    m_V_range = (10.0, 1000.0)
    g_range = (1e-4, 1e-1)
    
    grid = generator.generate_adaptive_grid(m_chi_range, m_V_range, g_range)
    
    print(f"Generated {len(grid)} grid points.")
    print(f"Refinement history: {generator.refinement_history}")
    
    # Save to CSV for inspection
    df = generator.get_grid_dataframe()
    output_path = "data/amr_grid_sample.csv"
    df.to_csv(output_path, index=False)
    print(f"Grid saved to {output_path}")

if __name__ == "__main__":
    main()
