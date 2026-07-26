"""
Generate Verified Synthetic Base Data for Meta-Analysis Simulation.

This script creates a fallback dataset when real Cochrane data fetch fails.
It generates synthetic study data based on parameters derived from Jackson et al., 2010,
ensuring the pipeline can proceed without fabrication of results during execution.

Parameters:
- Mean effect: 0.5
- SE distribution: LogNormal
- Study count: 20

Output:
- data/raw/cochrane_base_synthetic.csv
"""
import os
import csv
import random
from pathlib import Path
from typing import List, Dict, Any
import numpy as np

# Ensure reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# Task Parameters
MEAN_EFFECT = 0.5
STUDY_COUNT = 20
# LogNormal parameters chosen to generate realistic SEs for meta-analysis
# mu=0, sigma=0.5 generates a distribution of SEs centered around 1.0 with reasonable spread
LOGNORM_MU = 0.0
LOGNORM_SIGMA = 0.5

def generate_synthetic_base_data(
    n_studies: int = STUDY_COUNT,
    mean_effect: float = MEAN_EFFECT,
    lognorm_mu: float = LOGNORM_MU,
    lognorm_sigma: float = LOGNORM_SIGMA,
    seed: int = SEED
) -> List[Dict[str, Any]]:
    """
    Generate synthetic meta-analysis base data.

    Args:
        n_studies: Number of studies to generate.
        mean_effect: The target mean effect size.
        lognorm_mu: Mu parameter for LogNormal distribution of Standard Errors.
        lognorm_sigma: Sigma parameter for LogNormal distribution of Standard Errors.
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries containing study data.
    """
    random.seed(seed)
    np.random.seed(seed)

    data = []
    for i in range(n_studies):
        study_id = f"STUDY_{i+1:04d}"

        # Generate Standard Error from LogNormal distribution
        se = np.random.lognormal(mean=lognorm_mu, sigma=lognorm_sigma)
        # Ensure SE is positive and not too small to avoid numerical issues
        se = max(se, 0.01)

        # Calculate Variance (SE^2)
        variance = se ** 2

        # Generate Effect Size around the mean with noise based on the SE
        # This simulates a study observing an effect with that specific precision
        effect_size = np.random.normal(loc=mean_effect, scale=se)

        # Sample size is inversely related to variance (simplified model)
        # Larger variance -> smaller sample size. We use a heuristic to map variance to N.
        # Assuming typical variance ~ 1/N for large N, N ~ 1/variance.
        # We add noise to make it realistic and avoid N=1 or N=0.
        base_n = int(1.0 / variance) if variance > 0 else 100
        # Clamp N to reasonable bounds [10, 10000]
        sample_size = max(10, min(10000, base_n + int(np.random.normal(0, base_n * 0.1))))

        data.append({
            "study_id": study_id,
            "effect_size": round(effect_size, 6),
            "variance": round(variance, 8),
            "sample_size": sample_size
        })

    return data

def save_to_csv(data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the generated data to a CSV file.

    Args:
        data: List of dictionaries containing study data.
        output_path: Path to the output CSV file.
    """
    if not data:
        raise ValueError("No data to save.")

    fieldnames = ["study_id", "effect_size", "variance", "sample_size"]

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    """Main entry point for the script."""
    # Define output path relative to project root
    # Assuming script is run from project root or code/scripts
    project_root = Path(__file__).resolve().parent.parent.parent
    output_dir = project_root / "data" / "raw"
    output_file = output_dir / "cochrane_base_synthetic.csv"

    print(f"Generating synthetic base data with {STUDY_COUNT} studies...")
    print(f"Parameters: Mean Effect={MEAN_EFFECT}, SE~LogNormal({LOGNORM_MU}, {LOGNORM_SIGMA})")

    try:
        synthetic_data = generate_synthetic_base_data(
            n_studies=STUDY_COUNT,
            mean_effect=MEAN_EFFECT,
            lognorm_mu=LOGNORM_MU,
            lognorm_sigma=LOGNORM_SIGMA,
            seed=SEED
        )

        save_to_csv(synthetic_data, output_file)

        print(f"Successfully generated and saved synthetic data to: {output_file}")
        print(f"Total records: {len(synthetic_data)}")

        # Verify the file exists and is not empty
        if not output_file.exists():
            raise FileNotFoundError(f"Output file {output_file} was not created.")
        
        with open(output_file, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                raise ValueError("Output file is empty or contains only headers.")
        
        print("Verification passed: File exists and contains data.")

    except Exception as e:
        print(f"Error generating synthetic base data: {e}")
        raise

if __name__ == "__main__":
    main()
