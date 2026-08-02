"""
T013b: Generate Multi-L PR Dataset.

Runs PR computation for all disorder widths W in config.W_LIST and all
system sizes L in config.L_LIST. Aggregates results into a single JSON file.

Output: data/processed/pr_raw_multiL.json
"""
import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

# Project imports based on API surface
from code.config import get_config
from code.generate_hamiltonian import generate_hamiltonian
from code.analyze_pr import compute_eigenstates, compute_participation_ratio
from code.logger import get_logger, log_residual_decorator, inject_log_residual
from code.storage_utils import log_provenance_entry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_multiL_pr_dataset():
    """
    Generate PR dataset for all combinations of W and L.
    """
    config = get_config()
    W_list = config['W_LIST']
    L_list = config['L_LIST']
    num_realizations = config['NUM_REALIZATIONS']
    seed = config['SEED']

    output_dir = Path(config['DATA_PROCESSED_DIR'])
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'pr_raw_multiL.json'

    logger.info(f"Starting Multi-L PR Dataset generation.")
    logger.info(f"Config: W_LIST={W_list}, L_LIST={L_list}, N_REAL={num_realizations}, SEED={seed}")

    all_results = []

    # Initialize NumericalLogger for residuals
    numerical_logger = get_logger()

    # Set global seed for reproducibility
    np.random.seed(seed)

    for W in W_list:
        for L in L_list:
            logger.info(f"Processing W={W}, L={L}")
            
            for r_idx in range(num_realizations):
                # Determine realization seed
                # Using a deterministic seed generation based on W, L, and r_idx
                # to ensure reproducibility across runs if config seed is fixed
                current_seed = seed + int(W * 1000) + L * 100 + r_idx
                np.random.seed(current_seed)

                try:
                    # 1. Generate Hamiltonian (T005 logic)
                    H = generate_hamiltonian(L, W, seed=current_seed)
                    
                    # Log provenance
                    log_provenance_entry(
                        realization_index=r_idx,
                        seed=current_seed,
                        W=W,
                        L=L,
                        artifact_type="hamiltonian"
                    )

                    # 2. Compute Eigenstates (T012 logic)
                    # We need eigenvalues and eigenvectors for the PR calculation
                    # Use full diagonalization as per T012/T016 logic (fallback to sparse if needed)
                    try:
                        eigenvalues, eigenvectors = compute_eigenstates(H)
                    except Exception as e:
                        logger.warning(f"Eigenstate computation failed for W={W}, L={L}, r={r_idx}: {e}")
                        continue

                    # 3. Compute PR for eigenstates near E=0 (|E| < 0.1)
                    # Filter indices
                    mask = np.abs(eigenvalues) < 0.1
                    relevant_eigenvalues = eigenvalues[mask]
                    relevant_eigenvectors = eigenvectors[:, mask]

                    for i, ev in enumerate(relevant_eigenvalues):
                        psi = relevant_eigenvectors[:, i]
                        
                        # Compute PR
                        pr_val = compute_participation_ratio(psi)
                        
                        # Log residual/convergence if applicable (T017b hooks)
                        # For eigenvalue problem, we log the norm of the residual H*psi - E*psi
                        residual = H @ psi - ev * psi
                        norm_residual = np.linalg.norm(residual)
                        
                        # Inject logging
                        inject_log_residual(numerical_logger, norm_residual, flag=True)

                        # Store result
                        result_entry = {
                            "W": float(W),
                            "L": int(L),
                            "realization_index": int(r_idx),
                            "energy": float(ev),
                            "pr": float(pr_val)
                        }
                        all_results.append(result_entry)

                    logger.debug(f"Completed realization {r_idx}/{num_realizations} for W={W}, L={L}")

                except Exception as e:
                    logger.error(f"Failed to process W={W}, L={L}, r={r_idx}: {e}", exc_info=True)
                    # Continue to next realization to ensure robustness (SC-006)
                    continue

    # Write output
    logger.info(f"Writing {len(all_results)} results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)

    logger.info("Multi-L PR Dataset generation complete.")
    return output_path

def main():
    output_path = generate_multiL_pr_dataset()
    print(f"Output written to: {output_path}")

if __name__ == "__main__":
    main()
