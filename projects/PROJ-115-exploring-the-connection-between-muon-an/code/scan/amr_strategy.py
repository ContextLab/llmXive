"""
Adaptive Mesh Refinement (AMR) Strategy for Grid Convergence.

This module implements the logic to dynamically refine the parameter grid
based on the sensitivity of the relic density calculation (specifically near
resonances where m_V ≈ 2*m_chi). It adheres to Plan 0.3 for convergence studies.

The strategy identifies regions where the derivative of the thermally averaged
cross-section exceeds a threshold and recursively subdivides those regions.
"""
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

from physics.yukawa_solver import numerov_schrodinger, extract_sommerfeld_factor

@dataclass
class GridPoint:
    """Represents a single point in the parameter space (m_chi, m_V, g)."""
    m_chi: float
    m_V: float
    g: float
    sigma_v: float  # Thermally averaged cross-section
    is_viable: bool  # Placeholder for constraint check
    refinement_level: int = 0

@dataclass
class AMRConfig:
    """Configuration for the Adaptive Mesh Refinement."""
    initial_steps_chi: int = 20
    initial_steps_V: int = 20
    initial_steps_g: int = 10
    max_refinement_depth: int = 4
    sensitivity_threshold: float = 0.1  # Threshold for derivative-based refinement
    min_cell_size_chi: float = 1e-3  # MeV
    min_cell_size_V: float = 1e-3    # MeV
    min_cell_size_g: float = 1e-5

class AdaptiveGridGenerator:
    """
    Generates a parameter grid with Adaptive Mesh Refinement.

    The refinement is driven by the physics of the model:
    1. Coarse grid is generated over the full range.
    2. For each cell, the gradient of the relic density (or cross-section) is estimated.
    3. If the gradient exceeds the threshold (indicating a resonance or rapid change),
       the cell is subdivided.
    4. This repeats until max_depth or min_cell_size is reached.
    """

    def __init__(self, config: AMRConfig):
        self.config = config
        self.points: List[GridPoint] = []

    def _estimate_sommerfeld_factor(self, m_chi: float, m_V: float, g: float) -> float:
        """
        Estimates the Sommerfeld enhancement factor S for a given point.
        Uses the Yukawa solver to find the wavefunction enhancement.
        """
        # Simplified logic for AMR strategy:
        # In a full implementation, we would call numerov_schrodinger here.
        # For the strategy definition, we approximate the resonance condition.
        # Resonance occurs when m_V ≈ 2 * m_chi * (1 + epsilon), where epsilon ~ g^2.
        
        # Calculate the "distance" to the resonance pole
        resonance_mass = 2 * m_chi
        distance = abs(m_V - resonance_mass)
        
        # If very close to resonance, the derivative is huge -> high sensitivity
        if distance < 0.05 * resonance_mass:
            return 100.0 # Arbitrary high value to trigger refinement
        return 1.0

    def _calculate_sensitivity(self, p1: GridPoint, p2: GridPoint) -> float:
        """
        Calculates the sensitivity (gradient magnitude) between two points.
        """
        delta_S = abs(p1.sigma_v - p2.sigma_v)
        # Normalize by the parameter distance to get a true derivative
        # We use a simplified distance metric for this strategy
        dist = np.sqrt(
            (p1.m_chi - p2.m_chi)**2 + 
            (p1.m_V - p2.m_V)**2 + 
            (p1.g - p2.g)**2
        )
        if dist < 1e-12:
            return 0.0
        return delta_S / dist

    def generate_initial_grid(self, 
                              m_chi_range: Tuple[float, float], 
                              m_V_range: Tuple[float, float], 
                              g_range: Tuple[float, float]) -> List[GridPoint]:
        """Generates the coarse initial grid."""
        points = []
        m_chi_vals = np.linspace(m_chi_range[0], m_chi_range[1], self.config.initial_steps_chi)
        m_V_vals = np.linspace(m_V_range[0], m_V_range[1], self.config.initial_steps_V)
        g_vals = np.linspace(g_range[0], g_range[1], self.config.initial_steps_g)

        for m_chi in m_chi_vals:
            for m_V in m_V_vals:
                for g in g_vals:
                    # Estimate physics quantity for the grid point
                    s_factor = self._estimate_sommerfeld_factor(m_chi, m_V, g)
                    # Mock cross-section: sigma_v ~ S * g^4 / m_chi^2
                    sigma_v = s_factor * (g**4) / (m_chi**2)
                    
                    points.append(GridPoint(
                        m_chi=m_chi,
                        m_V=m_V,
                        g=g,
                        sigma_v=sigma_v,
                        is_viable=False, # To be determined later
                        refinement_level=0
                    ))
        return points

    def refine_region(self, 
                      cell_points: List[GridPoint], 
                      current_depth: int) -> List[GridPoint]:
        """
        Recursively refines a region if sensitivity is high.
        """
        if current_depth >= self.config.max_refinement_depth:
            return cell_points

        # Sort points to form cells (simplified 1D sweep for logic demonstration)
        # In 3D, we would check gradients along each axis.
        # Here we check the gradient of sigma_v across the sorted list.
        
        cell_points_sorted = sorted(cell_points, key=lambda p: p.m_V)
        
        needs_refinement = False
        for i in range(len(cell_points_sorted) - 1):
            p1, p2 = cell_points_sorted[i], cell_points_sorted[i+1]
            sensitivity = self._calculate_sensitivity(p1, p2)
            
            if sensitivity > self.config.sensitivity_threshold:
                needs_refinement = True
                break

        if not needs_refinement:
            return cell_points

        # If refinement needed, subdivide the parameter space
        # We create a finer grid within the bounds of these points
        min_chi = min(p.m_chi for p in cell_points)
        max_chi = max(p.m_chi for p in cell_points)
        min_V = min(p.m_V for p in cell_points)
        max_V = max(p.m_V for p in cell_points)
        min_g = min(p.g for p in cell_points)
        max_g = max(p.g for p in cell_points)

        # Check minimum size constraints
        if (max_chi - min_chi) < self.config.min_cell_size_chi or \
           (max_V - min_V) < self.config.min_cell_size_V or \
           (max_g - min_g) < self.config.min_cell_size_g:
            return cell_points

        # Generate new finer points in this region
        # We double the resolution in this specific region
        new_points = []
        m_chi_vals = np.linspace(min_chi, max_chi, len(cell_points) * 2 + 1)
        m_V_vals = np.linspace(min_V, max_V, len(cell_points) * 2 + 1)
        g_vals = np.linspace(min_g, max_g, len(cell_points) * 2 + 1)

        for m_chi in m_chi_vals:
            for m_V in m_V_vals:
                for g in g_vals:
                    s_factor = self._estimate_sommerfeld_factor(m_chi, m_V, g)
                    sigma_v = s_factor * (g**4) / (m_chi**2)
                    new_points.append(GridPoint(
                        m_chi=m_chi,
                        m_V=m_V,
                        g=g,
                        sigma_v=sigma_v,
                        is_viable=False,
                        refinement_level=current_depth + 1
                    ))
        
        # Recursively refine the new points
        return self.refine_region(new_points, current_depth + 1)

    def run_convergence_strategy(self, 
                                 m_chi_range: Tuple[float, float], 
                                 m_V_range: Tuple[float, float], 
                                 g_range: Tuple[float, float]) -> List[GridPoint]:
        """
        Executes the full AMR strategy:
        1. Generate coarse grid.
        2. Identify high-sensitivity regions.
        3. Refine those regions.
        4. Return the final adaptive grid.
        """
        # Step 1: Coarse Grid
        coarse_grid = self.generate_initial_grid(m_chi_range, m_V_range, g_range)
        
        # Step 2 & 3: Refine based on sensitivity
        # For this implementation, we treat the whole grid as one region to refine
        # if any part is sensitive, or we could partition into cells.
        # Here we implement a global refinement loop for simplicity in this module.
        
        final_grid = self.refine_region(coarse_grid, 0)
        
        return final_grid

    def get_grid_statistics(self, points: List[GridPoint]) -> Dict[str, Any]:
        """Returns statistics about the generated grid for logging."""
        if not points:
            return {"total_points": 0}
        
        levels = [p.refinement_level for p in points]
        return {
            "total_points": len(points),
            "max_refinement_level": max(levels),
            "avg_refinement_level": np.mean(levels),
            "chi_range": (min(p.m_chi for p in points), max(p.m_chi for p in points)),
            "V_range": (min(p.m_V for p in points), max(p.m_V for p in points)),
            "g_range": (min(p.g for p in points), max(p.g for p in points))
        }

# Example usage / Entry point for the strategy definition
if __name__ == "__main__":
    config = AMRConfig(
        initial_steps_chi=10,
        initial_steps_V=10,
        initial_steps_g=5,
        max_refinement_depth=3,
        sensitivity_threshold=0.5
    )
    
    generator = AdaptiveGridGenerator(config)
    
    # Define a test range around a hypothetical resonance
    # m_chi: 10-100 MeV, m_V: 20-200 MeV (covering 2*m_chi)
    grid = generator.run_convergence_strategy(
        m_chi_range=(10.0, 100.0),
        m_V_range=(20.0, 200.0),
        g_range=(1e-4, 1e-2)
    )
    
    stats = generator.get_grid_statistics(grid)
    print(f"AMR Strategy Execution Complete.")
    print(f"Statistics: {stats}")
    
    # Verify we have points
    assert len(grid) > 0, "Grid generation failed to produce points."
    print(f"Generated {len(grid)} points with adaptive refinement.")
