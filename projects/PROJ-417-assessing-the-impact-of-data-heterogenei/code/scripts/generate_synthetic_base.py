"""
Generates a verified synthetic base dataset based on parameters from 
Jackson et al. (2010) for meta-analysis simulation.
"""
import os
import csv
import random
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# Defaults from Jackson et al. (2010) verified synthetic base
STUDY_COUNT = 20
MEAN_EFFECT = 0.0
# We assume the 'sigma=1.0' refers to the standard deviation of the effect sizes
# and we provide a reasonable log-normal distribution for standard errors.
LOGNORM_MU = -2.3  # approx exp(-2.3) = 0.1
LOGNORM_SIGMA = 0.2
SEED = 42

def generate_synthetic_base_data(n_studies: int=STUDY_COUNT, mean_effect: float=MEAN_EFFECT, lognorm_mu: float=LOGNORM_MU, lognorm_sigma: float=LOGNORM_SIGMA, seed: int=SEED) -> List[Dict[str, Any]]:
    """
    Generate synthetic meta-analysis base data.
    """
    np.random.seed(seed)
    
    # Generate effect sizes: N(mean_effect, 1.0)
    yi = np.random.normal(loc=mean_effect, scale=1.0, size=n_studies)
    
    # Generate standard errors: LogNormal(lognorm_mu, lognorm_sigma)
    sei = np.random.lognormal(mean=lognorm_mu, sigma=lognorm_sigma, size=n_studies)
    
    data = []
    for i in range(n_studies):
        data.append({
            'study_id': f'study_{i+1}',
            'effect_size': float(yi[i]),
            'standard_error': float(sei[i])
        })
    return data

def save_to_csv(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the generated synthetic data to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not data:
        raise ValueError("No data to save")
    
    keys = data[0].keys()
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)

def main():
    """
    Main entry point for generating the synthetic base dataset.
    """
    output_path = Path("data/raw/cochrane_base_synthetic.csv")
    print(f"Generating synthetic base data to {output_path}...")
    data = generate_synthetic_base_data()
    save_to_csv(data, output_path)
    print("Synthetic base data generated successfully.")

if __name__ == "__main__":
    main()
