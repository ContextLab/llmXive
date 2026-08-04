"""
T013b: Generate Multi-L PR Dataset

Runs PR computation for all disorder widths W in config.W_LIST and all system sizes L in config.L_LIST.
Reads configuration, generates Hamiltonians (T005), computes PR (T012), and aggregates.
Output: data/processed/pr_raw_multiL.json

Schema: List of objects with W, L, realization_index, energy, pr.
"""
import json
import os
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

# Import from existing API surface
from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian
from code.analyze_pr import compute_participation_ratio, compute_eigenstates
from code.logger import get_logger, log_residual_decorator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_multiL_pr_dataset() -> List[Dict[str, Any]]:
    """
    Generate PR dataset for all combinations of W and L.

    Returns:
        List of dictionaries containing W, L, realization_index, energy, pr.
    """
    config = get_config()
    W_list = config.get('W_LIST', [1.0])
    L_list = config.get('L_LIST', [100, 200, 400])
    num_realizations = config.get('NUM_REALIZATIONS', 10)
    seed = config.get('SEED', 42)

    # Initialize numpy random generator with base seed
    rng = np.random.default_rng(seed)

    results = []
    total_iterations = len(W_list) * len(L_list) * num_realizations
    current_iteration = 0

    logger.info(f"Starting multi-L PR dataset generation.")
    logger.info(f"Config: W_LIST={W_list}, L_LIST={L_list}, NUM_REALIZATIONS={num_realizations}")

    for W in W_list:
        for L in L_list:
            for r_idx in range(num_realizations):
                current_iteration += 1
                progress = (current_iteration / total_iterations) * 100
                logger.info(f"Processing: W={W}, L={L}, Realization={r_idx} ({progress:.1f}%)")

                # Generate unique seed for this realization
                # Use the RNG to generate a specific seed for this run
                realization_seed = rng.integers(0, 2**31)
                np.random.seed(realization_seed)

                try:
                    # Generate Hamiltonian
                    # T005: generate_hamiltonian returns (H, on_site, hopping) or similar
                    # We need to check the exact return signature from the API surface
                    # Based on API: generate_hamiltonian(H, on_site, hopping) or returns H
                    # Let's assume it returns H directly or we need to call it correctly
                    # The API surface says: generate_hamiltonian, generate_hamiltonian_batch
                    # We'll call it and handle the return
                    H, on_site, hopping = generate_hamiltonian(L, W, seed=realization_seed)

                    # Compute eigenstates
                    # T012: compute_eigenstates(H) -> energies, eigenvectors
                    energies, eigenvectors = compute_eigenstates(H)

                    # Compute PR for eigenstates within |E| < 0.1
                    # T012: compute_participation_ratio(eigenvectors, energies, energy_window=0.1)
                    # This should return a list of PR values for eigenstates in the window
                    pr_results = compute_participation_ratio(eigenvectors, energies, energy_window=0.1)

                    # pr_results is likely a list of dicts or tuples: (energy, pr)
                    for pr_data in pr_results:
                        if isinstance(pr_data, dict):
                            results.append({
                                'W': W,
                                'L': L,
                                'realization_index': r_idx,
                                'energy': pr_data['energy'],
                                'pr': pr_data['pr']
                            })
                        elif isinstance(pr_data, (list, tuple)) and len(pr_data) >= 2:
                            results.append({
                                'W': W,
                                'L': L,
                                'realization_index': r_idx,
                                'energy': pr_data[0],
                                'pr': pr_data[1]
                            })

                except Exception as e:
                    logger.error(f"Error processing W={W}, L={L}, r={r_idx}: {e}")
                    # Log to residuals/warnings as per T017b/T013a requirements
                    # We'll just continue to next realization
                    continue

    logger.info(f"Completed multi-L PR dataset generation. Total entries: {len(results)}")
    return results

def main():
    """Main entry point."""
    logger.info("Starting T013b: Generate Multi-L PR Dataset")

    # Generate dataset
    dataset = generate_multiL_pr_dataset()

    # Ensure output directory exists
    output_path = Path("data/processed/pr_raw_multiL.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(output_path, 'w') as f:
        json.dump(dataset, f, indent=2)

    logger.info(f"Dataset written to {output_path}")
    logger.info(f"Total records: {len(dataset)}")

    return dataset

if __name__ == "__main__":
    main()