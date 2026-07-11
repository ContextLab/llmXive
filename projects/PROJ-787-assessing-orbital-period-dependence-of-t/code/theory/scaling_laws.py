"""
Scaling laws for exoplanet radius gap analysis.

This module defines the Owen & Wu (photoevaporation) and Ginzburg et al. (2018)
(core-powered mass loss) scaling law equations as Gaussian distributions.
Parameters are loaded from code/theory/config.yaml as specified in FR-007.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Tuple, Any, Optional
from dataclasses import dataclass
import numpy as np
from scipy import stats

# Ensure the parent directory is in the path for imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.config import load_config, get_config

logger = logging.getLogger(__name__)

@dataclass
class TheoreticalDistribution:
    """Represents a theoretical scaling law as a Gaussian distribution."""
    name: str
    mean_slope: float
    std_slope: float
    description: str

    def get_distribution(self) -> stats._continuous_distns.norm_frozen:
        """Returns a frozen scipy normal distribution for this theoretical model."""
        return stats.norm(loc=self.mean_slope, scale=self.std_slope)

    def pdf(self, x: float) -> float:
        """Calculate the probability density function at x."""
        return self.get_distribution().pdf(x)

    def cdf(self, x: float) -> float:
        """Calculate the cumulative distribution function at x."""
        return self.get_distribution().cdf(x)

    def sample(self, size: int = 1) -> np.ndarray:
        """Draw random samples from this distribution."""
        return self.get_distribution().rvs(size=size)

def load_theoretical_laws(config_path: Optional[str] = None) -> Dict[str, TheoreticalDistribution]:
    """
    Load theoretical scaling law parameters from the configuration file.

    Args:
        config_path: Optional path to the config YAML file. If None, uses default.

    Returns:
        A dictionary mapping theory names to TheoreticalDistribution objects.
    """
    config = load_config(config_path)
    
    # Extract Owen & Wu parameters (Photoevaporation)
    owen_wu_params = config.get('owen_wu', {})
    owen_wu = TheoreticalDistribution(
        name="owen_wu",
        mean_slope=owen_wu_params.get('mean_slope', -0.11),
        std_slope=owen_wu_params.get('std_slope', 0.02),
        description=owen_wu_params.get('description', "Photoevaporation model (Owen & Wu)")
    )

    # Extract Ginzburg parameters (Core-powered mass loss)
    ginzburg_params = config.get('ginzburg', {})
    ginzburg = TheoreticalDistribution(
        name="ginzburg",
        mean_slope=ginzburg_params.get('mean_slope', -0.15),
        std_slope=ginzburg_params.get('std_slope', 0.03),
        description=ginzburg_params.get('description', "Core-powered mass loss model (Ginzburg et al. 2018)")
    )

    logger.info(f"Loaded Owen & Wu distribution: mean={owen_wu.mean_slope:.2f}, std={owen_wu.std_slope:.2f}")
    logger.info(f"Loaded Ginzburg distribution: mean={ginzburg.mean_slope:.2f}, std={ginzburg.std_slope:.2f}")

    return {
        "owen_wu": owen_wu,
        "ginzburg": ginzburg
    }

def get_theoretical_overlap(
    dist1: TheoreticalDistribution, 
    dist2: TheoreticalDistribution,
    num_samples: int = 100000
) -> float:
    """
    Estimate the overlap area between two theoretical distributions via Monte Carlo.

    Args:
        dist1: First theoretical distribution.
        dist2: Second theoretical distribution.
        num_samples: Number of samples for Monte Carlo estimation.

    Returns:
        Estimated overlap area (0.0 to 1.0).
    """
    samples1 = dist1.sample(num_samples)
    samples2 = dist2.sample(num_samples)
    
    # Count how many times the samples overlap significantly
    # This is a simplified overlap metric based on sample intersection
    overlap_count = 0
    for s1, s2 in zip(samples1, samples2):
        # Check if the distance between samples is within 1 std of the combined variance
        combined_std = np.sqrt(dist1.std_slope**2 + dist2.std_slope**2)
        if abs(s1 - s2) < combined_std:
            overlap_count += 1
    
    return overlap_count / num_samples

def main():
    """
    Main entry point for testing the scaling laws module.
    Loads distributions, prints summary statistics, and runs a basic overlap check.
    """
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting Scaling Laws Module Test")

    try:
        # Load theoretical distributions
        theories = load_theoretical_laws()

        if not theories:
            logger.error("Failed to load any theoretical distributions.")
            sys.exit(1)

        # Print distribution details
        for name, theory in theories.items():
            logger.info(f"--- {theory.name} ---")
            logger.info(f"Description: {theory.description}")
            logger.info(f"Mean Slope: {theory.mean_slope:.4f}")
            logger.info(f"Std Slope: {theory.std_slope:.4f}")
            
            # Verify distribution properties
            sample = theory.sample(1000)
            logger.info(f"Sample Mean (1000 draws): {np.mean(sample):.4f}")
            logger.info(f"Sample Std (1000 draws): {np.std(sample):.4f}")

        # Calculate overlap between the two theories
        if "owen_wu" in theories and "ginzburg" in theories:
            overlap = get_theoretical_overlap(
                theories["owen_wu"], 
                theories["ginzburg"]
            )
            logger.info(f"Estimated overlap between Owen & Wu and Ginzburg: {overlap:.4f}")

        logger.info("Scaling laws module test completed successfully.")

    except Exception as e:
        logger.error(f"Error during scaling laws execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
