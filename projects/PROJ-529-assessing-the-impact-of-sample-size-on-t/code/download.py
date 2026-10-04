import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Import from project utilities
from utils.seeds import SeedManager
from utils.exceptions import DataAcquisitionError
from config import is_simulation_mode, is_real_mode, get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simulation Parameters based on Ioannidis et al. (2008)
IOANNIDIS_PARAMS = {
    "tau_squared": 0.04,
    "mean_effect": 0.3,
    "bias": 0.1,
    "study_count_range": [3, 50],
    "seed": 42
}

def generate_synthetic_meta_analysis(
    meta_id: str,
    study_count: int,
    tau_squared: float = 0.04,
    mean_effect: float = 0.3,
    bias: float = 0.1,
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Generates a synthetic meta-analysis dataset based on Ioannidis et al. (2008) parameters.
    
    Args:
        meta_id: Unique identifier for this meta-analysis.
        study_count: Number of studies in the meta-analysis.
        tau_squared: Between-study variance.
        mean_effect: True underlying effect size.
        bias: Systematic bias to introduce.
        seed: Random seed for reproducibility.
        
    Returns:
        List of dictionaries containing 'effect_size' and 'se' for each study.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # True effect size for this meta-analysis (drawn from distribution around mean)
    true_effect = np.random.normal(mean_effect, np.sqrt(tau_squared))
    
    studies = []
    for i in range(study_count):
        # Generate study-level effect size
        # Effect = True Effect + Bias + Between-Study Variance + Sampling Error
        between_study_error = np.random.normal(0, np.sqrt(tau_squared))
        
        # Sampling error variance (SE^2) - typically decreases with study size
        # Simulate study sizes between 20 and 500
        study_n = np.random.randint(20, 500)
        se = np.sqrt(1/study_n + 0.01)  # Add small constant to avoid zero variance
        
        # Observed effect = True effect + Bias + Random noise
        observed_effect = true_effect + bias + np.random.normal(0, se)
        
        studies.append({
            "study_id": f"{meta_id}_study_{i+1}",
            "effect_size": float(observed_effect),
            "se": float(se),
            "n": int(study_n)
        })
    
    return studies

def save_synthetic_data(
    data_dir: Path,
    params: Dict[str, Any],
    num_meta_analyses: int = 50
) -> List[Path]:
    """
    Generates and saves synthetic meta-analysis data files.
    
    Args:
        data_dir: Directory to save the generated data.
        params: Simulation parameters.
        num_meta_analyses: Number of meta-analyses to generate.
        
    Returns:
        List of paths to generated data files.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []
    
    # Save parameters
    params_path = data_dir / "simulation_params.json"
    with open(params_path, 'w') as f:
        json.dump(params, f, indent=2)
    logger.info(f"Saved simulation parameters to {params_path}")
    
    # Generate meta-analyses
    for i in range(num_meta_analyses):
        meta_id = f"sim_meta_{i+1:03d}"
        
        # Random study count within range
        study_count = np.random.randint(
            params["study_count_range"][0],
            params["study_count_range"][1] + 1
        )
        
        # Generate synthetic data
        studies = generate_synthetic_meta_analysis(
            meta_id=meta_id,
            study_count=study_count,
            tau_squared=params["tau_squared"],
            mean_effect=params["mean_effect"],
            bias=params["bias"],
            seed=params["seed"] + i
        )
        
        # Save to CSV
        file_path = data_dir / f"{meta_id}.csv"
        with open(file_path, 'w') as f:
            # Write header
            f.write("study_id,effect_size,se,n\n")
            # Write data
            for study in studies:
                f.write(f"{study['study_id']},{study['effect_size']:.6f},{study['se']:.6f},{study['n']}\n")
        
        generated_files.append(file_path)
        logger.info(f"Generated {meta_id} with {study_count} studies")
    
    logger.info(f"Generated {num_meta_analyses} synthetic meta-analyses")
    return generated_files

def run_simulation_fallback(
    data_dir: Path,
    params: Optional[Dict[str, Any]] = None,
    num_meta_analyses: int = 50
) -> bool:
    """
    Executes the simulation fallback when real data acquisition fails.
    
    Args:
        data_dir: Directory to save generated data.
        params: Optional custom parameters (uses Ioannidis defaults if None).
        num_meta_analyses: Number of meta-analyses to generate.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        logger.info("Starting simulation fallback...")
        
        # Use default parameters if not provided
        if params is None:
            params = IOANNIDIS_PARAMS.copy()
        
        # Ensure seed is set
        if "seed" not in params:
            params["seed"] = 42
        
        # Generate and save data
        generated_files = save_synthetic_data(data_dir, params, num_meta_analyses)
        
        if not generated_files:
            raise DataAcquisitionError("No synthetic data files were generated.")
        
        logger.info(f"Simulation fallback completed successfully. Generated {len(generated_files)} files.")
        return True
        
    except Exception as e:
        logger.error(f"Simulation fallback failed: {str(e)}")
        raise DataAcquisitionError(f"Simulation fallback failed: {str(e)}")

def main():
    """Main entry point for synthetic data generation."""
    # Get configuration
    config = get_config()
    
    # Determine data directory
    data_root = Path(config.get("data_root", "data"))
    raw_dir = data_root / "raw"
    
    # Check if we should run simulation
    if is_real_mode():
        logger.warning("Real mode is enabled. Skipping simulation fallback.")
        return
    
    logger.info("Running simulation fallback as real data acquisition failed.")
    
    # Run simulation
    success = run_simulation_fallback(raw_dir)
    
    if success:
        logger.info("Simulation fallback completed successfully.")
    else:
        logger.error("Simulation fallback failed.")
        raise DataAcquisitionError("Simulation fallback failed to generate data.")

if __name__ == "__main__":
    main()
