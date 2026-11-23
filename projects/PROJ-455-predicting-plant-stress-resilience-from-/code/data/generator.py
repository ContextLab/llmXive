import os
import random
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)

def generate_synthetic_data(
    n_samples: int,
    stress_type: str,
    missing_rate: float = 0.05,
    seed: int = 42
) -> str:
    """
    Generate synthetic metabolomic data with ground-truth stress vectors.
    
    Args:
        n_samples: Number of samples to generate.
        stress_type: Type of stress ('drought', 'salinity', 'heat', 'cold').
        missing_rate: Proportion of values to set as NaN (must be < 0.1 for acceptance).
        seed: Random seed for reproducibility.
        
    Returns:
        Path to the generated Parquet file.
    """
    # Set seeds for reproducibility
    np.random.seed(seed)
    random.seed(seed)
    
    logger.info(f"Generating {n_samples} synthetic samples for {stress_type} stress (seed={seed})")
    
    # Define metabolites relevant to plant stress responses
    metabolites = [
        "proline", "glutamate", "glycine_betaine", "ABA", "jasmonic_acid",
        "salicylic_acid", "glutathione", "ascorbate", "sucrose", "glucose",
        "fructose", "starch", "malate", "citrate", "alpha_ketoglutarate",
        "GABA", "serine", "glycine", "threonine", "arginine"
    ]
    
    # Define stress-specific response patterns (ground truth)
    stress_patterns = {
        "drought": {"proline": 2.5, "ABA": 3.0, "sucrose": 1.8, "glutathione": 1.5},
        "salinity": {"proline": 2.2, "glycine_betaine": 2.8, "ABA": 1.5, "glutathione": 1.8},
        "heat": {"HSP_related_metabolites": 2.0, "ABA": 1.2, "sucrose": 1.5},
        "cold": {"sucrose": 2.0, "raffinose": 2.5, "ABA": 1.8}
    }
    
    # Base concentrations (arbitrary units)
    base_concentrations = {m: np.random.uniform(10, 100) for m in metabolites}
    
    # Generate samples
    data = []
    for i in range(n_samples):
        sample = {
            "sample_id": f"sample_{i:04d}",
            "stress_type": stress_type,
            "stress_vector_seed": seed,
        }
        
        # Apply stress-specific modifications
        pattern = stress_patterns.get(stress_type, {})
        for met, factor in pattern.items():
            if met in base_concentrations:
                sample[met] = base_concentrations[met] * factor
            else:
                # For metabolites not in base list, use random base
                sample[met] = np.random.uniform(10, 100) * factor
        
        # Fill in remaining metabolites
        for met in metabolites:
            if met not in sample:
                sample[met] = base_concentrations.get(met, np.random.uniform(10, 100))
        
        # Generate recovery metrics (correlated with stress response)
        # Higher proline/ABA generally correlates with better recovery in drought
        if stress_type == "drought":
            recovery_score = (sample.get("proline", 0) * 0.3 + 
                            sample.get("ABA", 0) * 0.3 + 
                            sample.get("glutathione", 0) * 0.2 +
                            np.random.normal(0, 10))
        elif stress_type == "salinity":
            recovery_score = (sample.get("glycine_betaine", 0) * 0.4 + 
                            sample.get("proline", 0) * 0.2 +
                            np.random.normal(0, 10))
        else:
            recovery_score = np.random.normal(50, 15)
        
        # Normalize recovery index to 0-1
        sample["recovery_metric"] = max(0, min(100, recovery_score))
        sample["recovery_index"] = (sample["recovery_metric"] - 20) / 80  # Rough normalization
        sample["recovery_index"] = max(0.0, min(1.0, sample["recovery_index"]))
        
        data.append(sample)
    
    df = pd.DataFrame(data)
    
    # Introduce missing values
    if missing_rate > 0:
        mask = np.random.random(df.shape) < missing_rate
        # Don't make sample_id, stress_type, or recovery metrics missing
        for col in ["sample_id", "stress_type", "stress_vector_seed", "recovery_metric", "recovery_index"]:
            if col in df.columns:
                df.loc[:, col] = df[col].where(~mask[df.columns.get_loc(col)], np.nan)
        
        # Apply mask to metabolite columns
        metabolite_cols = [col for col in df.columns if col not in 
                         ["sample_id", "stress_type", "stress_vector_seed", "recovery_metric", "recovery_index"]]
        for col in metabolite_cols:
            df.loc[mask[df.columns.get_loc(col)], col] = np.nan
    
    # Save to Parquet
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "data/raw"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"synthetic_{stress_type}_{seed}_{timestamp}.parquet")
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Synthetic data saved to {output_path}")
    
    return output_path

def generate_lodo_synthetic_datasets(
    n_datasets: int,
    stress_types: List[str]
) -> List[str]:
    """
    Generate multiple distinct synthetic datasets for LODO validation.
    
    Each dataset has a unique stress_vector_seed to ensure independence.
    
    Args:
        n_datasets: Number of datasets to generate.
        stress_types: List of stress types to include.
        
    Returns:
        List of paths to generated Parquet files.
    """
    logger.info(f"Generating {n_datasets} LODO synthetic datasets")
    
    output_paths = []
    base_seed = 42
    
    for i in range(n_datasets):
        # Ensure unique seed for each dataset
        dataset_seed = base_seed + i * 1000
        stress_type = stress_types[i % len(stress_types)]
        
        # Generate dataset with varying sample size
        n_samples = np.random.randint(150, 300)
        missing_rate = np.random.uniform(0.02, 0.08)
        
        output_path = generate_synthetic_data(
            n_samples=n_samples,
            stress_type=stress_type,
            missing_rate=missing_rate,
            seed=dataset_seed
        )
        output_paths.append(output_path)
        
        logger.info(f"Generated dataset {i+1}/{n_datasets}: {stress_type}, seed={dataset_seed}")
    
    return output_paths
