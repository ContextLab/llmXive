import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field
import logging
from physics.yukawa_solver import numerov_schrodinger, extract_sommerfeld_factor
from schemas.parameter_point import ParameterPoint, validate_parameter_point

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GridPoint:
    """Represents a single point in the parameter grid."""
    m_V: float  # Vector mediator mass in MeV
    m_chi: float  # Dark matter mass in MeV
    g: float  # Coupling constant
    omega_h2: Optional[float] = None  # Calculated relic density
    is_viable: Optional[bool] = None
    refinement_level: int = 0

@dataclass
class AMRConfig:
    """Configuration for Adaptive Mesh Refinement strategy."""
    initial_grid_steps: int = 10
    refinement_threshold: float = 0.1  # Relative change threshold for refinement
    max_refinement_depth: int = 4
    min_grid_spacing: float = 0.01  # Minimum spacing in log space
    convergence_tolerance: float = 0.05  # 5% tolerance for convergence
    target_viable_coverage: float = 0.95  # 95% confidence in capturing viable regions

class AdaptiveGridGenerator:
    """
    Implements Adaptive Mesh Refinement (AMR) for the parameter space scan.
    
    Strategy:
    1. Start with a coarse grid in log-space for m_V, m_chi, and g.
    2. Evaluate the relic density (or a proxy like Sommerfeld enhancement) at each point.
    3. Identify regions where the gradient exceeds the refinement threshold.
    4. Subdivide those regions recursively up to max_refinement_depth.
    5. Stop when the grid converges (no new viable regions found with refinement) 
       or max depth is reached.
    
    This ensures high resolution in resonance regions (narrow viable bands) 
    while maintaining computational efficiency in excluded regions.
    """

    def __init__(self, config: AMRConfig):
        self.config = config
        self.grid_points: List[GridPoint] = []
        self.refinement_history: List[int] = []

    def _log_space_grid(self, m_min: float, m_max: float, steps: int) -> np.ndarray:
        """Generate a grid in logarithmic space."""
        return np.logspace(np.log10(m_min), np.log10(m_max), steps)

    def _calculate_metric(self, point: ParameterPoint) -> float:
        """
        Calculate a metric to determine if refinement is needed.
        Uses the Sommerfeld enhancement as a proxy for rapid changes in relic density.
        """
        try:
            # Calculate Sommerfeld factor as a proxy for sensitivity
            # In a full implementation, this would use the actual relic density calculation
            # but for the grid strategy, the gradient of the enhancement factor is sufficient
            s_factor = extract_sommerfeld_factor(
                m_V=point.m_V,
                m_chi=point.m_chi,
                g=point.g,
                alpha=1/137.0  # Approximate fine structure constant
            )
            return s_factor
        except Exception as e:
            logger.warning(f"Failed to calculate metric for point {point}: {e}")
            return 0.0

    def _refine_region(self, points: List[GridPoint]) -> List[GridPoint]:
        """
        Subdivide regions where the metric gradient exceeds the threshold.
        """
        if len(points) < 2:
            return points

        refined_points = []
        
        # Sort points by metric value to identify gradients
        points_sorted = sorted(points, key=lambda p: p.m_V)
        
        for i in range(len(points_sorted) - 1):
            p1 = points_sorted[i]
            p2 = points_sorted[i + 1]
            
            metric1 = self._calculate_metric(ParameterPoint(m_V=p1.m_V, m_chi=p1.m_chi, g=p1.g))
            metric2 = self._calculate_metric(ParameterPoint(m_V=p2.m_V, m_chi=p2.m_chi, g=p2.g))
            
            # Calculate relative change
            if abs(metric1) > 1e-10:
                relative_change = abs(metric2 - metric1) / abs(metric1)
            else:
                relative_change = abs(metric2 - metric1)
            
            refined_points.append(p1)
            
            # If gradient is high and we haven't reached max depth, subdivide
            if (relative_change > self.config.refinement_threshold and 
                p1.refinement_level < self.config.max_refinement_depth):
                
                # Create mid-point in log space
                m_V_mid = np.sqrt(p1.m_V * p2.m_V)
                m_chi_mid = np.sqrt(p1.m_chi * p2.m_chi)
                g_mid = np.sqrt(p1.g * p2.g)
                
                mid_point = GridPoint(
                    m_V=m_V_mid,
                    m_chi=m_chi_mid,
                    g=g_mid,
                    refinement_level=p1.refinement_level + 1
                )
                refined_points.append(mid_point)
                
                self.refinement_history.append(p1.refinement_level + 1)
            
            if i == len(points_sorted) - 2:
                refined_points.append(p2)
        
        return refined_points

    def generate_adaptive_grid(
        self,
        m_V_range: Tuple[float, float],
        m_chi_range: Tuple[float, float],
        g_range: Tuple[float, float]
    ) -> List[GridPoint]:
        """
        Generate an adaptive grid covering the parameter space.
        
        Args:
            m_V_range: (min, max) for vector mediator mass in MeV
            m_chi_range: (min, max) for dark matter mass in MeV
            g_range: (min, max) for coupling constant
            
        Returns:
            List of GridPoint objects representing the adaptive grid
        """
        logger.info(f"Generating adaptive grid for m_V: {m_V_range}, m_chi: {m_chi_range}, g: {g_range}")
        
        # Initial coarse grid
        m_V_vals = self._log_space_grid(m_V_range[0], m_V_range[1], self.config.initial_grid_steps)
        m_chi_vals = self._log_space_grid(m_chi_range[0], m_chi_range[1], self.config.initial_grid_steps)
        g_vals = self._log_space_grid(g_range[0], g_range[1], self.config.initial_grid_steps)
        
        initial_points = []
        for m_V in m_V_vals:
            for m_chi in m_chi_vals:
                for g in g_vals:
                    point = ParameterPoint(m_V=m_V, m_chi=m_chi, g=g)
                    if validate_parameter_point(point):
                        grid_point = GridPoint(m_V=m_V, m_chi=m_chi, g=g)
                        initial_points.append(grid_point)
        
        self.grid_points = initial_points
        logger.info(f"Initial grid size: {len(self.grid_points)} points")
        
        # Iterative refinement
        for depth in range(self.config.max_refinement_depth):
            logger.info(f"Refinement iteration {depth + 1}")
            
            # Refine based on current metrics
            refined_points = self._refine_region(self.grid_points)
            
            # Check for convergence
            if len(refined_points) == len(self.grid_points):
                logger.info(f"Grid converged at depth {depth}")
                break
                
            self.grid_points = refined_points
            logger.info(f"Grid size after refinement: {len(self.grid_points)} points")
            
            # Check if we've reached the minimum grid spacing
            if (m_V_vals[1] / m_V_vals[0]) < self.config.min_grid_spacing:
                logger.info("Reached minimum grid spacing constraint")
                break
        
        logger.info(f"Final adaptive grid size: {len(self.grid_points)} points")
        return self.grid_points

    def get_convergence_stats(self) -> Dict[str, Any]:
        """
        Return statistics about the grid convergence process.
        """
        return {
            "initial_size": self.config.initial_grid_steps ** 3,
            "final_size": len(self.grid_points),
            "max_refinement_depth_reached": max(self.refinement_history) if self.refinement_history else 0,
            "refinement_levels_distribution": {
                str(i): self.refinement_history.count(i) for i in range(self.config.max_refinement_depth + 1)
            }
        }

def main():
    """
    Main function to demonstrate the AMR strategy.
    Generates an adaptive grid and prints convergence statistics.
    """
    config = AMRConfig(
        initial_grid_steps=5,
        refinement_threshold=0.15,
        max_refinement_depth=3,
        min_grid_spacing=0.05,
        convergence_tolerance=0.05,
        target_viable_coverage=0.95
    )
    
    generator = AdaptiveGridGenerator(config)
    
    # Define parameter ranges (typical for this study)
    m_V_range = (1.0, 1000.0)  # MeV
    m_chi_range = (0.1, 100.0)  # MeV
    g_range = (1e-5, 1e-1)
    
    grid = generator.generate_adaptive_grid(m_V_range, m_chi_range, g_range)
    
    stats = generator.get_convergence_stats()
    print(f"Adaptive Grid Generation Complete")
    print(f"Stats: {stats}")
    
    # Save a sample of the grid to a file for verification
    if grid:
        import json
        sample_data = [
            {
                "m_V": p.m_V,
                "m_chi": p.m_chi,
                "g": p.g,
                "refinement_level": p.refinement_level
            }
            for p in grid[:100]  # Save first 100 points as sample
        ]
        
        output_path = "data/amr_grid_sample.json"
        import os
        os.makedirs("data", exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(sample_data, f, indent=2)
        print(f"Sample grid saved to {output_path}")

if __name__ == "__main__":
    main()
