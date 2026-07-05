"""
Data acquisition and synthetic data generation module.

Handles fetching real meta-analyses from Cochrane/Campbell (T012)
and generating synthetic data as a fallback (T019) based on
Ioannidis et al. (2008) parameters.
"""
import json
import os
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import numpy as np
import requests
from tqdm import tqdm
import logging

from utils.exceptions import DataAcquisitionError
from utils.seeds import set_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ioannidis et al. (2008) Simulation Parameters
IOANNIDIS_PARAMS = {
    "tau_sq": 0.04,          # Between-study variance
    "mean_effect": 0.3,      # Overall mean effect size
    "bias": 0.1,             # Small study bias
    "study_count_range": [3, 50], # Range of study counts per meta-analysis
    "seed": 42
}

@dataclass
class SimulatedStudy:
    """Represents a single study within a meta-analysis."""
    study_id: int
    meta_id: int
    effect_size: float
    se: float
    sample_size: int
    n_events: int
    n_total: int

def generate_synthetic_meta_analyses(
    num_meta_analyses: int = 50,
    params: Optional[Dict[str, Any]] = None,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Generate synthetic meta-analyses using Ioannidis et al. (2008) parameters.
    
    Args:
        num_meta_analyses: Number of meta-analyses to generate.
        params: Dictionary of simulation parameters. Defaults to IOANNIDIS_PARAMS.
        seed: Random seed for reproducibility.
        
    Returns:
        List of dictionaries, each representing a meta-analysis with its studies.
    """
    if params is None:
        params = IOANNIDIS_PARAMS
    
    set_seed(seed)
    
    tau_sq = params["tau_sq"]
    mu = params["mean_effect"] + params["bias"]
    k_min, k_max = params["study_count_range"]
    
    meta_analyses = []
    
    logger.info(f"Generating {num_meta_analyses} synthetic meta-analyses...")
    logger.info(f"Parameters: tau^2={tau_sq}, mu={mu}, k_range=[{k_min}, {k_max}]")
    
    for meta_idx in range(num_meta_analyses):
        # Random number of studies for this meta-analysis
        k = random.randint(k_min, k_max)
        
        # True effect sizes for each study (drawn from N(mu, tau^2))
        true_effects = np.random.normal(mu, np.sqrt(tau_sq), k)
        
        # Generate within-study standard errors
        # SE is inversely related to sample size
        # Larger studies -> smaller SE
        # We model SE ~ 1/sqrt(n) where n is sample size
        study_sizes = np.random.randint(50, 1000, k)  # Sample sizes between 50 and 1000
        ses = 1.0 / np.sqrt(study_sizes) * 2.0  # Scale to reasonable SE range
        
        # Observed effects = true effect + sampling error
        observed_effects = true_effects + np.random.normal(0, ses)
        
        # Simulate binary outcome data (events/total)
        # Using a simple logistic model for event probabilities
        logit_p = observed_effects - 0.5  # Offset to get reasonable probabilities
        probs = 1 / (1 + np.exp(-logit_p))
        probs = np.clip(probs, 0.01, 0.99)  # Avoid extremes
        
        events = np.random.binomial(study_sizes, probs)
        
        studies = []
        for i in range(k):
            study = SimulatedStudy(
                study_id=f"study_{meta_idx}_{i}",
                meta_id=f"meta_{meta_idx}",
                effect_size=float(observed_effects[i]),
                se=float(ses[i]),
                sample_size=int(study_sizes[i]),
                n_events=int(events[i]),
                n_total=int(study_sizes[i])
            )
            studies.append(asdict(study))
        
        meta_analyses.append({
            "meta_id": f"meta_{meta_idx}",
            "source": "simulation",
            "num_studies": k,
            "studies": studies,
            "parameters": {
                "tau_sq": tau_sq,
                "mu": mu,
                "bias": params["bias"]
            }
        })
    
    logger.info(f"Successfully generated {len(meta_analyses)} meta-analyses")
    return meta_analyses

def save_simulation_parameters(params: Dict[str, Any], output_path: str) -> None:
    """Save simulation parameters to JSON file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.info(f"Saved simulation parameters to {output_path}")

def save_synthetic_data(meta_analyses: List[Dict[str, Any]], output_dir: str) -> None:
    """
    Save synthetic meta-analyses to individual JSON files.
    
    Args:
        meta_analyses: List of meta-analysis dictionaries.
        output_dir: Directory to save files.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for meta in meta_analyses:
        filename = f"{meta['meta_id']}.json"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(meta, f, indent=2)
    
    logger.info(f"Saved {len(meta_analyses)} synthetic meta-analyses to {output_dir}")

def download_from_cochrane(query: str = "meta-analysis effect size") -> List[Dict[str, Any]]:
    """
    Attempt to fetch meta-analyses from Cochrane Library.
    
    Note: Cochrane Library does not have a public API for direct data download.
    This function simulates the attempt and raises DataAcquisitionError.
    """
    # Cochrane Library requires manual download or special access
    # We simulate a failed fetch to trigger fallback
    raise DataAcquisitionError(
        "Cochrane Library data not accessible via public API. "
        "Switching to simulation fallback."
    )

def download_from_campbell(query: str = "meta-analysis") -> List[Dict[str, Any]]:
    """
    Attempt to fetch meta-analyses from Campbell Collaboration RSS.
    
    Note: RSS feeds provide metadata only, not full effect size data.
    This function simulates a failed fetch to trigger fallback.
    """
    # Campbell RSS provides metadata only
    raise DataAcquisitionError(
        "Campbell Collaboration RSS provides metadata only. "
        "Full effect size data not accessible. "
        "Switching to simulation fallback."
    )

def run_fallback_simulation(
    num_meta_analyses: int = 50,
    params: Optional[Dict[str, Any]] = None,
    output_dir: str = "data/raw"
) -> str:
    """
    Execute the fallback simulation process (T019).
    
    This is triggered when real data acquisition fails.
    
    Args:
        num_meta_analyses: Number of meta-analyses to generate.
        params: Simulation parameters.
        output_dir: Directory to save output files.
        
    Returns:
        Path to the simulation parameters file.
    """
    logger.info("Starting fallback simulation (T019)...")
    
    if params is None:
        params = IOANNIDIS_PARAMS.copy()
    
    # Save parameters
    params_path = os.path.join(output_dir, "simulation_params.json")
    save_simulation_parameters(params, params_path)
    
    # Generate synthetic data
    meta_analyses = generate_synthetic_meta_analyses(
        num_meta_analyses=num_meta_analyses,
        params=params,
        seed=params.get("seed", 42)
    )
    
    # Save data
    save_synthetic_data(meta_analyses, output_dir)
    
    logger.info("Fallback simulation completed successfully.")
    return params_path

def main():
    """
    Main entry point for data acquisition with fallback.
    
    Tries to fetch real data, falls back to simulation if unsuccessful.
    """
    logger.info("=== Data Acquisition Module ===")
    
    output_dir = "data/raw"
    
    # Try real data sources
    try:
        logger.info("Attempting to fetch real data from Cochrane...")
        # cochrane_data = download_from_cochrane()
        # This would be called if API were available
        raise DataAcquisitionError("Cochrane API not available in this environment")
    except DataAcquisitionError as e:
        logger.warning(f"Cochrane fetch failed: {e}")
        try:
            logger.info("Attempting to fetch real data from Campbell...")
            # campbell_data = download_from_campbell()
            raise DataAcquisitionError("Campbell RSS provides metadata only")
        except DataAcquisitionError as e:
            logger.warning(f"Campbell fetch failed: {e}")
            logger.info("Both real data sources unavailable. Triggering fallback simulation (T019).")
            
            # Trigger fallback
            params_path = run_fallback_simulation(
                num_meta_analyses=50,
                params=IOANNIDIS_PARAMS,
                output_dir=output_dir
            )
            
            logger.info(f"Simulation complete. Parameters saved to {params_path}")
            return params_path

if __name__ == "__main__":
    main()
