"""
Synthetic Data Generator for CI Fallback.

Generates a statistically realistic dataset for CI validation when real data
is missing and the pipeline is running in a CI environment.

Uses Multivariate Normal distributions for continuous variables and
Bernoulli for binary variables.
"""
import argparse
import logging
import sys
import os
import random
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parents[3]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import numpy as np
import pandas as pd
from src.utils.io_helpers import FatalError

logger = logging.getLogger(__name__)

class SyntheticDataGenerator:
    """Generates synthetic data matching contracts/dataset.schema.yaml."""

    @staticmethod
    def check_real_data_exists(data_dir: str = "data/raw") -> bool:
        """
        Check if real data files exist in the specified directory.
        
        Args:
            data_dir: Relative path to the data directory.
            
        Returns:
            bool: True if real data files are found, False otherwise.
        """
        full_path = project_root / data_dir
        if not full_path.exists():
            return False
        
        # Look for specific expected real data files (not synthetic ones)
        # Assuming real data comes from LSMS-ISA and has specific naming
        expected_real_files = [
            "malawi_lsms.csv",
            "tanzania_lsms.csv",
            "analysis_dataset.csv" # If already processed
        ]
        
        for filename in expected_real_files:
            if (full_path / filename).exists():
                return True
                
        return False

    @staticmethod
    def generate(output_path: Path, n_samples: int = 350, seed: int = 42) -> None:
        """
        Generate synthetic dataset.
        
        Args:
            output_path: Path to save the generated CSV.
            n_samples: Number of records to generate.
            seed: Random seed for reproducibility.
        """
        random.seed(seed)
        np.random.seed(seed)
        
        logger.info(f"Generating {n_samples} synthetic records...")
        
        # 1. Define Correlations and Distributions
        # Continuous: land_size, education_level, extension_visits
        # Binary: finance_access, practice_*
        # Derived: CSA_Index, Stability_Score, HFIAS
        
        # Base continuous variables
        # land_size ~ LogNormal (skewed positive)
        land_size = np.random.lognormal(mean=1.5, sigma=0.8, size=n_samples)
        
        # education_level (ordinal 0-12) - approximated by truncated normal
        education = np.clip(np.random.normal(loc=6.0, scale=3.0, size=n_samples), 0, 12).astype(int)
        
        # extension_visits (count)
        extension_visits = np.random.poisson(lam=3, size=n_samples)
        
        # 2. Binary Variables with Correlations
        # finance_access: positively correlated with education
        prob_finance = 0.3 + 0.05 * education
        prob_finance = np.clip(prob_finance, 0, 1)
        finance_access = np.random.binomial(1, prob_finance)
        
        # practice_mixed_farming
        practice_mixed = np.random.binomial(1, 0.6, size=n_samples)
        
        # practice_terracing (correlated with land_size and education)
        prob_terracing = 0.2 + 0.1 * (land_size > 1.0).astype(float) + 0.02 * education
        prob_terracing = np.clip(prob_terracing, 0, 1)
        practice_terracing = np.random.binomial(1, prob_terracing)
        
        # practice_conservation_tillage
        practice_conservation = np.random.binomial(1, 0.4, size=n_samples)
        
        # practice_agroforestry
        practice_agroforestry = np.random.binomial(1, 0.3, size=n_samples)
        
        # extension_visits (already generated, but ensure non-negative)
        extension_visits = np.maximum(0, extension_visits)
        
        # 3. Derived Metrics
        # CSA_Index: Sum of binary practices (0-4)
        csa_index = (practice_mixed + practice_terracing + 
                     practice_conservation + practice_agroforestry)
        
        # Stability_Score: Inverse of CV of NDVI (simulated)
        # Simulate NDVI stability based on practices and land size
        # Higher practices -> higher stability
        base_stability = 0.5
        practice_boost = 0.1 * csa_index
        land_stability = 0.1 * np.log(land_size + 1)
        noise = np.random.normal(0, 0.1, size=n_samples)
        stability_score = base_stability + practice_boost + land_stability + noise
        stability_score = np.clip(stability_score, 0.1, 1.0) # Normalize to 0-1 approx
        
        # HFIAS: Food security score (lower is better, but let's say 0-27 scale)
        # Correlated with education and finance
        hlias_base = 15 - (0.5 * education) - (2 * finance_access)
        hlias_noise = np.random.normal(0, 3, size=n_samples)
        hlias = hlias_base + hlias_noise
        hlias = np.clip(hlias, 0, 27).astype(float)
        
        # hlias (integer version for schema)
        hlias_int = np.clip(np.round(hlias), 0, 27).astype(int)
        
        # 4. Coordinates and IDs
        # Simulate Malawi/Tanzania region coordinates
        # Malawi approx: -13 to -17 lat, 33 to 36 lon
        latitude = np.random.uniform(-17, -13, size=n_samples)
        longitude = np.random.uniform(33, 36, size=n_samples)
        
        # Village ID: derived from coordinates (rounded grid)
        buffer_size = 1.0 # km approx in deg (very rough)
        village_lat = np.round(latitude / buffer_size) * buffer_size
        village_lon = np.round(longitude / buffer_size) * buffer_size
        village_ids = [f"V{int(la)}_{int(lo)}" for la, lo in zip(village_lat, village_lon)]
        
        # Household IDs
        household_ids = list(range(10000, 10000 + n_samples))
        
        # 5. Construct DataFrame
        df = pd.DataFrame({
            'household_id': household_ids,
            'latitude': latitude,
            'longitude': longitude,
            'land_size': land_size,
            'education_level': education,
            'finance_access': finance_access.astype(bool),
            'practice_mixed_farming': practice_mixed.astype(bool),
            'practice_terracing': practice_terracing.astype(bool),
            'practice_conservation_tillage': practice_conservation.astype(bool),
            'practice_agroforestry': practice_agroforestry.astype(bool),
            'extension_visits': extension_visits,
            'hlias': hlias_int,
            'CSA_Index': csa_index.astype(float),
            'Stability_Score': stability_score,
            'HFIAS': hlias,
            'village_id': village_ids
        })
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Synthetic data saved to {output_path}")

def main() -> None:
    """CLI entry point for the generator."""
    parser = argparse.ArgumentParser(description="Generate synthetic data for CI fallback.")
    parser.add_argument("--output", type=str, default="data/raw/synthetic_analysis_dataset.csv",
                        help="Output path for the CSV file.")
    parser.add_argument("--n", type=int, default=350, help="Number of samples.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    
    try:
        SyntheticDataGenerator.generate(output_path, n_samples=args.n, seed=args.seed)
    except Exception as e:
        raise FatalError(f"Synthetic data generation failed: {e}")

if __name__ == "__main__":
    main()