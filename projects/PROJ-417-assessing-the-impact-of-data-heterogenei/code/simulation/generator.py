import json
import math
import random
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from scipy import stats
from pathlib import Path

# Import logging utility
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback for direct execution or different import context
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)

class SimulationConfig:
    def __init__(self, tau2: float, n_replicates: int, seed: int = 42):
        self.tau2 = tau2
        self.n_replicates = n_replicates
        self.seed = seed

class SimulationResult:
    def __init__(self, data: List[Dict[str, Any]], config: SimulationConfig):
        self.data = data
        self.config = config

def load_base_data_structure(source_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads the base data structure from a CSV or returns a synthetic structure
    if no path is provided (for testing purposes).
    """
    if source_path and Path(source_path).exists():
        # In a real scenario, parse the CSV
        # For now, we return a placeholder structure if file exists
        # Actual parsing logic would go here
        logger.info(f"Loading base data from {source_path}")
        # Placeholder: In real implementation, read CSV and convert to list of dicts
        return {
            "studies": [
                {"id": f"study_{i}", "n": 50, "se": 0.2}
                for i in range(20)
            ]
        }
    else:
        # Return a synthetic base structure for testing/generation when no file exists
        # This allows the generator to run without the raw data file for unit tests
        # The actual T010 task would enforce loading from data/raw/cochrane_base.csv
        logger.warning("No base data file provided or found. Using synthetic structure.")
        return {
            "studies": [
                {"id": f"study_{i}", "n": np.random.randint(20, 100), "se": np.random.uniform(0.1, 0.5)}
                for i in range(10)
            ]
        }

def create_replicate(base_structure: Dict[str, Any], target_tau2: float, seed: int) -> Dict[str, Any]:
    """
    Creates a single replicate dataset with the specified between-study variance (tau^2).
    
    Args:
        base_structure: Dictionary containing study characteristics (n, se).
        target_tau2: The target between-study variance to inject.
        seed: Random seed for this specific replicate.
    
    Returns:
        Dictionary representing the generated dataset with true effects and observed effects.
    """
    random.seed(seed)
    np.random.seed(seed)
    
    studies = []
    true_effects = []
    
    # True overall effect (mu) - fixed for this simulation
    mu = 0.5 
    
    # Generate true effects for each study
    for study in base_structure["studies"]:
        # True effect for this study: theta_i ~ N(mu, tau^2)
        # If tau^2 is 0, all theta_i = mu
        if target_tau2 > 0:
            theta_i = np.random.normal(mu, math.sqrt(target_tau2))
        else:
            theta_i = mu
        
        # Observed effect: y_i ~ N(theta_i, se_i^2)
        se_i = study["se"]
        y_i = np.random.normal(theta_i, se_i)
        
        studies.append({
            "id": study["id"],
            "n": study["n"],
            "se": se_i,
            "true_effect": theta_i,
            "observed_effect": y_i
        })
        true_effects.append(theta_i)
    
    return {
        "replicate_id": seed,
        "true_tau2": target_tau2,
        "true_mu": mu,
        "studies": studies,
        "observed_effects": [s["observed_effect"] for s in studies],
        "true_effects": true_effects,
        "se_list": [s["se"] for s in studies]
    }

def generate_synthetic_meta_analysis(config: SimulationConfig, base_data: Optional[Dict[str, Any]] = None) -> SimulationResult:
    """
    Generates multiple replicates of meta-analysis datasets.
    
    Args:
        config: SimulationConfig with target tau^2, number of replicates, and seed.
        base_data: Optional base data structure. If None, loads from default or synthetic.
    
    Returns:
        SimulationResult containing list of generated datasets.
    """
    if base_data is None:
        base_data = load_base_data_structure()
    
    random.seed(config.seed)
    np.random.seed(config.seed)
    
    replicates = []
    for i in range(config.n_replicates):
        replicate_seed = config.seed + i
        replicate = create_replicate(base_data, config.tau2, replicate_seed)
        replicates.append(replicate)
        logger.info(f"Generated replicate {i+1}/{config.n_replicates} with tau^2={config.tau2}")
    
    return SimulationResult(data=replicates, config=config)

def validate_simulation_output(result: SimulationResult) -> bool:
    """
    Validates that the simulation output conforms to expected schema.
    """
    for replicate in result.data:
        if "true_tau2" not in replicate:
            logger.error("Missing true_tau2 in replicate")
            return False
        if "studies" not in replicate:
            logger.error("Missing studies in replicate")
            return False
        for study in replicate["studies"]:
            if "observed_effect" not in study or "true_effect" not in study:
                logger.error("Missing effect fields in study")
                return False
    return True

def main():
    """
    Entry point for running the generator directly.
    """
    # Example usage
    config = SimulationConfig(tau2=0.5, n_replicates=10, seed=42)
    result = generate_synthetic_meta_analysis(config)
    
    if validate_simulation_output(result):
        # Save to JSON
        output_path = Path("data/results/simulation_raw.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            # Convert to JSON serializable format
            json_data = [
                {
                    "replicate_id": r["replicate_id"],
                    "true_tau2": r["true_tau2"],
                    "true_mu": r["true_mu"],
                    "n_studies": len(r["studies"]),
                    "observed_effects": r["observed_effects"]
                }
                for r in result.data
            ]
            json.dump(json_data, f, indent=2)
        
        logger.info(f"Saved {len(result.data)} replicates to {output_path}")
    else:
        logger.error("Validation failed")

if __name__ == "__main__":
    main()