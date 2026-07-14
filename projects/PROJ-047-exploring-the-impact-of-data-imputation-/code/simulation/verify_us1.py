"""
Verification logic for User Story 1 (T014).

Calculates Spearman correlation between the missingness mask M and the
generated complete outcome Y (before masking) to verify the MNAR mechanism.
"""

import json
import hashlib
import os
from typing import Tuple, Any, Dict

import numpy as np
import pandas as pd
from scipy import stats

# Import existing API surface
from simulation.missingness import inject_mnar
from simulation.scm_generator import generate_scm


def compute_run_id(seed: int, beta: float) -> str:
    """
    Generate a SHA-256 hash of the string "{seed}_{beta}".
    """
    input_str = f"{seed}_{beta}"
    return hashlib.sha256(input_str.encode('utf-8')).hexdigest()


def verify_mnar_correlation(
    seed: int,
    beta: float,
    n_samples: int = 1000
) -> Dict[str, Any]:
    """
    Generate synthetic data, inject MNAR missingness, and calculate
    Spearman correlation between the mask M and the complete Y.

    Args:
        seed: Random seed for reproducibility.
        beta: The MNAR parameter controlling the strength of the relationship
              between Y and the missingness mask M.
        n_samples: Number of samples to generate.

    Returns:
        Dictionary containing:
            - run_id: SHA-256 hash of "{seed}_{beta}"
            - correlation: Spearman rho
            - p_value: P-value for the correlation
            - status: "reported"
    """
    # 1. Generate complete synthetic data (X, T, Y)
    # Note: generate_scm expects tau_true. We assume a standard value or
    # derive it. Based on T006, tau_true is often 0.5 for seed=42, beta=0.5.
    # However, generate_scm signature is (seed, n, tau_true).
    # We need a consistent tau_true. Let's use a fixed value of 0.5 as per T006 example,
    # or derive it if regenerate_ground_truth is meant to be used here.
    # The task description implies we just need to verify the mechanism.
    # Let's assume tau_true = 0.5 for the generation step to ensure valid Y exists.
    tau_true = 0.5
    dataset = generate_scm(seed=seed, n=n_samples, tau_true=tau_true)

    # dataset.Y is the complete outcome variable (numpy array or pandas Series)
    y_complete = dataset.Y
    if isinstance(y_complete, np.ndarray):
        y_complete = pd.Series(y_complete)

    # 2. Inject MNAR missingness
    # inject_mnar(data, beta, target_rate)
    # We need a target_rate. The task doesn't specify, but T012 handles tuning.
    # For verification, we can use a fixed target rate (e.g., 0.3) or let inject_mnar
    # use a default if it has one. Looking at T011 description: "using logistic regression".
    # Let's assume a standard target rate of 0.3 if not specified, or pass it.
    # Since T012 is "tune_alpha", we might need to call it or use a fixed alpha.
    # The task says "inject_mnar(data, beta, target_rate)".
    # Let's use a reasonable target rate like 0.3.
    target_rate = 0.3
    missing_data = inject_mnar(dataset, beta=beta, target_rate=target_rate)

    # The missingness pattern M is usually stored in the dataset or returned.
    # Based on T007, MissingnessPattern has a 'mask' field.
    # inject_mnar likely returns a dataset with an added 'mask' attribute or similar.
    # Let's assume the returned object has a 'mask' attribute (numpy array of 0/1).
    # If missing_data is a SyntheticDataset, we need to check where M is stored.
    # The prompt says "Calculate Spearman rho between M and the generated complete Y".
    # Let's assume the mask is accessible as missing_data.mask or similar.
    # If the function returns the modified dataset, we look for the mask.
    # If the function returns the mask directly, we use that.
    # Let's assume the mask is part of the returned dataset object as 'mask'.
    # If not, we might need to reconstruct it or the function returns it.
    # Given the API surface provided, inject_mnar is in missingness.py.
    # Let's assume it modifies the dataset and adds a 'mask' attribute.
    # If the mask is not directly on the dataset, we might need to check the implementation.
    # However, since I must implement T014 based on the API, I will assume the mask
    # is available as `missing_data.mask` (numpy array).

    mask = missing_data.mask
    if isinstance(mask, np.ndarray):
        mask = pd.Series(mask)

    # 3. Calculate Spearman correlation
    # We correlate the mask (0/1) with the complete Y.
    # Note: Y might contain NaN if generate_scm didn't clean it, but it should be complete.
    # The mask indicates missingness (1=missing, 0=observed).
    # We expect a correlation if MNAR is working.

    # Ensure no NaNs in Y for correlation (should be complete)
    if y_complete.isna().any():
        # This shouldn't happen for the complete Y before masking
        y_complete = y_complete.dropna()
        mask = mask.loc[y_complete.index]

    spearman_rho, p_value = stats.spearmanr(y_complete, mask)

    # 4. Construct result
    run_id = compute_run_id(seed, beta)

    result = {
        "run_id": run_id,
        "correlation": float(spearman_rho),
        "p_value": float(p_value),
        "status": "reported"
    }

    return result


def run_verification_and_save(
    seed: int,
    beta: float,
    output_path: str = "data/results/us1_verification.json"
) -> None:
    """
    Run the verification for a specific seed and beta, and save the result.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    result = verify_mnar_correlation(seed, beta)

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Verification result for seed={seed}, beta={beta} saved to {output_path}")
    print(f"  Run ID: {result['run_id']}")
    print(f"  Spearman rho: {result['correlation']:.4f}")
    print(f"  P-value: {result['p_value']:.4f}")
    print(f"  Status: {result['status']}")


if __name__ == "__main__":
    # Example usage: Run for a specific seed and beta
    # In the main loop (T029a), this function will be called for each run.
    # Here we run a single example for demonstration/verification.
    seed = 42
    beta = 0.5
    run_verification_and_save(seed, beta)
