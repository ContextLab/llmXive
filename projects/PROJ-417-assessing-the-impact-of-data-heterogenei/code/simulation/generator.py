"""
Simulation generator for synthetic meta-analysis datasets.

This module implements the core logic for generating synthetic data
based on real Cochrane base data structures, injecting specific
heterogeneity levels (tau^2).
"""

import json
import math
import random
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats

# Optional: Load real base data if available, otherwise use structure defaults
# T040 will provide the real data file. This handles the case where it's missing gracefully
# or uses a placeholder structure for testing the API.
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

from utils.logging import get_logger

logger = get_logger(__name__)


class SimulationConfig:
    """Configuration for a single simulation run."""
    def __init__(self, tau_squared: float, seed: int, n_replicates: int = 1):
        self.tau_squared = tau_squared
        self.seed = seed
        self.n_replicates = n_replicates

class SimulationResult:
    """Container for a single simulation replicate result."""
    def __init__(
        self,
        replicate_id: int,
        true_tau_squared: float,
        n_studies: int,
        effect_sizes: List[float],
        standard_errors: List[float],
        injected_seed: int
    ):
        self.replicate_id = replicate_id
        self.true_tau_squared = true_tau_squared
        self.n_studies = n_studies
        self.effect_sizes = effect_sizes
        self.standard_errors = standard_errors
        self.injected_seed = injected_seed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "replicate_id": self.replicate_id,
            "true_tau_squared": self.true_tau_squared,
            "n_studies": self.n_studies,
            "effect_sizes": self.effect_sizes,
            "standard_errors": self.standard_errors,
            "inject_seed": self.injected_seed
        }


def load_base_data_structure(filepath: str) -> List[Dict[str, float]]:
    """
    Loads the base data structure from a CSV file.
    Returns a list of dictionaries with 'effect' and 'se' keys.
    Falls back to a synthetic structure if file is missing (for T005 API test).
    """
    if not HAS_PANDAS:
        logger.warning("Pandas not installed. Using synthetic base structure.")
        return _generate_synthetic_base_structure()

    if not os.path.exists(filepath):
        logger.warning(f"Base data file {filepath} not found. Using synthetic structure.")
        return _generate_synthetic_base_structure()

    try:
        df = pd.read_csv(filepath)
        # Expect columns 'effect_size' and 'se' or similar
        # Normalize to expected keys
        if 'effect_size' in df.columns and 'se' in df.columns:
            return df[['effect_size', 'se']].to_dict(orient='records')
        elif 'effect' in df.columns and 'se' in df.columns:
            return df[['effect', 'se']].to_dict(orient='records')
        else:
            logger.error(f"Base data file {filepath} missing required columns.")
            return _generate_synthetic_base_structure()
    except Exception as e:
        logger.error(f"Error loading base data: {e}")
        return _generate_synthetic_base_structure()

def _generate_synthetic_base_structure() -> List[Dict[str, float]]:
    """Generates a synthetic base structure if real data is unavailable."""
    # Simulate a typical meta-analysis structure (e.g., 20 studies)
    n_studies = 20
    base_effects = np.random.normal(0.5, 0.1, n_studies)
    base_se = np.random.uniform(0.05, 0.2, n_studies)
    return [{"effect_size": float(e), "se": float(s)} for e, s in zip(base_effects, base_se)]

def create_replicate(
    base_data: List[Dict[str, float]],
    tau_squared: float,
    seed: int
) -> SimulationResult:
    """
    Creates a single simulation replicate by perturbing base data
    with the specified heterogeneity (tau^2).

    Args:
        base_data: List of dicts with 'effect_size' and 'se'.
        tau_squared: Target between-study variance.
        seed: Random seed for this replicate.

    Returns:
        SimulationResult object.
    """
    random.seed(seed)
    np.random.seed(seed)

    n_studies = len(base_data)
    if n_studies < 5:
        logger.warning(f"Small study count ({n_studies}) for seed {seed}. Flagging for exclusion.")

    # True effect sizes are drawn from N(mu, tau^2 + se^2)
    # We assume a global mu (e.g., 0.5) or calculate from base mean
    mu = np.mean([d['effect_size'] for d in base_data])

    observed_effects = []
    observed_se = []

    for i, study in enumerate(base_data):
        se_i = study['se']
        # Total variance = se^2 + tau^2
        total_var = se_i**2 + tau_squared
        if total_var <= 0:
            total_var = 1e-6 # Avoid numerical instability

        # Draw new effect size
        new_effect = np.random.normal(mu, math.sqrt(total_var))
        observed_effects.append(float(new_effect))
        observed_se.append(float(se_i)) # SE usually fixed from study design in this model

    return SimulationResult(
        replicate_id=seed,
        true_tau_squared=tau_squared,
        n_studies=n_studies,
        effect_sizes=observed_effects,
        standard_errors=observed_se,
        injected_seed=seed
    )

def generate_synthetic_meta_analysis(
    base_data_path: str,
    tau_levels: List[float],
    replicates_per_level: int,
    output_path: str
) -> None:
    """
    Main entry point for generating the full simulation dataset.

    Args:
        base_data_path: Path to the real base CSV (T040 output).
        tau_levels: List of tau^2 levels to simulate.
        replicates_per_level: Number of replicates per level.
        output_path: Path to write the JSON output.
    """
    logger.info(f"Loading base data from {base_data_path}")
    base_data = load_base_data_structure(base_data_path)

    all_results = []
    global_id = 0

    for tau in tau_levels:
        logger.info(f"Generating {replicates_per_level} replicates for tau^2={tau}")
        for i in range(replicates_per_level):
            seed = global_id
            result = create_replicate(base_data, tau, seed)
            all_results.append(result.to_dict())
            global_id += 1

    # Write output
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info(f"Simulation complete. Output written to {output_path}")

def validate_simulation_output(filepath: str) -> bool:
    """
    Validates that the output JSON conforms to expected schema.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            return False

        required_keys = {'replicate_id', 'true_tau_squared', 'n_studies', 'effect_sizes', 'standard_errors'}
        for record in data:
            if not required_keys.issubset(record.keys()):
                return False
        return True
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False
