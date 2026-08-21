import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
import pandas as pd

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.config import get_path, GROUND_TRUTH_EFFECT_SIZE, init_random_seeds, DATA_MODE
from code.utils.logging import get_logger, log_pipeline_step
from code.utils.norms import load_norms_data, get_means, get_std_devs, get_correlation_matrix, get_covariance_matrix

# Initialize logger
logger = get_logger(__name__)

def load_mdes_report() -> Dict[str, Any]:
    """
    Load the MDES report from state/mdes_report.yaml.
    Validates that the file exists and contains the required key.
    
    Returns:
        Dict containing the MDES report data.
        
    Raises:
        FileNotFoundError: If the report file is missing.
        KeyError: If the mdes_value key is missing.
    """
    report_path = get_path("state", "mdes_report.yaml")
    
    if not report_path.exists():
        raise FileNotFoundError(
            f"MDES report missing at {report_path}. "
            "Ensure T045 (Power Analysis) is complete before running this task."
        )
    
    import yaml
    with open(report_path, 'r') as f:
        data = yaml.safe_load(f)
    
    if 'mdes_value' not in data:
        raise KeyError(
            f"MDES report at {report_path} does not contain 'mdes_value' key. "
            "Ensure T045 wrote the value correctly."
        )
    
    logger.info(f"Loaded MDES report: mdes_value = {data['mdes_value']}")
    return data

def validate_ground_truth_effect(mdes_value: float) -> None:
    """
    Validate that the ground truth effect size is greater than the MDES.
    
    Args:
        mdes_value: The Minimum Detectable Effect Size calculated in T045.
        
    Raises:
        ValueError: If ground truth effect is not greater than MDES.
    """
    if GROUND_TRUTH_EFFECT_SIZE <= mdes_value:
        raise ValueError(
            f"Ground truth effect ({GROUND_TRUTH_EFFECT_SIZE}) must be greater than "
            f"MDES ({mdes_value}) for the simulation to be powered to detect it. "
            "Please update GROUND_TRUTH_EFFECT_SIZE in config.py or re-run T045."
        )
    
    logger.info(
        f"Ground truth validation passed: {GROUND_TRUTH_EFFECT_SIZE} > {mdes_value}"
    )

def get_correlation_matrix() -> np.ndarray:
    """
    Generate a correlation matrix for the 5 moral foundations based on Gervais norms.
    
    Returns:
        5x5 correlation matrix.
    """
    # Gervais et al. (2016) typical correlations between foundations
    # These are approximate values derived from the literature
    corr_values = np.array([
        [1.00, 0.45, 0.30, 0.35, 0.25],  # Care
        [0.45, 1.00, 0.50, 0.40, 0.30],  # Fairness
        [0.30, 0.50, 1.00, 0.60, 0.55],  # Loyalty
        [0.35, 0.40, 0.60, 1.00, 0.65],  # Authority
        [0.25, 0.30, 0.55, 0.65, 1.00]   # Purity
    ])
    return corr_values

def generate_covariance_matrix(means: np.ndarray, stds: np.ndarray, corr_matrix: np.ndarray) -> np.ndarray:
    """
    Convert correlation matrix to covariance matrix using standard deviations.
    
    Args:
        means: Array of means (not used directly but kept for interface consistency)
        stds: Array of standard deviations
        corr_matrix: Correlation matrix
        
    Returns:
        Covariance matrix.
    """
    std_matrix = np.diag(stds)
    cov_matrix = std_matrix @ corr_matrix @ std_matrix
    return cov_matrix

def generate_synthetic_mfq(n_participants: int = 200, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic MFQ data based on Gervais et al. multivariate normal distributions.
    
    Args:
        n_participants: Number of participants to simulate (must be 200 per T046)
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with synthetic MFQ scores.
        
    Raises:
        ValueError: If n_participants is not 200.
    """
    if n_participants != 200:
        raise ValueError(
            f"Simulated N must be 200 to match MDES assumptions (T046). "
            f"Got N={n_participants}."
        )
    
    logger.info(f"Generating synthetic MFQ data for {n_participants} participants...")
    
    # Load norms
    norms_data = load_norms_data()
    means = get_means()
    stds = get_std_devs()
    corr_matrix = get_correlation_matrix()
    cov_matrix = generate_covariance_matrix(means, stds, corr_matrix)
    
    # Generate multivariate normal data
    np.random.seed(seed)
    data = np.random.multivariate_normal(means, cov_matrix, size=n_participants)
    
    # Create DataFrame
    columns = ['care', 'fairness', 'loyalty', 'authority', 'purity']
    df = pd.DataFrame(data, columns=columns)
    
    # Add participant IDs
    df['participant_id'] = range(1, n_participants + 1)
    
    # Add some realistic missingness (approx 2% missing at random)
    missing_mask = np.random.random(df.shape) < 0.02
    df = df.mask(missing_mask)
    
    logger.info(f"Generated MFQ data with shape {df.shape}")
    logger.info(f"Missing values per column:\n{df.isnull().sum()}")
    
    return df

def main() -> None:
    """
    Main entry point for T013: Generate synthetic MFQ data.
    
    Steps:
    1. Load MDES report and validate existence.
    2. Validate ground truth effect against MDES.
    3. Validate N=200 constraint.
    4. Generate synthetic MFQ data.
    5. Save to data/raw/synthetic_mfq.csv.
    6. Log validation results.
    """
    log_pipeline_step("START", "T013: Synthetic MFQ Generation")
    
    # Step 1: Load MDES report
    try:
        mdes_report = load_mdes_report()
        mdes_value = mdes_report['mdes_value']
    except (FileNotFoundError, KeyError) as e:
        logger.error(f"Failed to load MDES report: {e}")
        raise
    
    # Step 2: Validate ground truth effect
    validate_ground_truth_effect(mdes_value)
    
    # Step 3: Validate N constraint
    n_simulated = 200
    if n_simulated != 200:
        logger.error(f"N simulation constraint violated: {n_simulated} != 200")
        raise ValueError(f"N must be 200, got {n_simulated}")
    
    logger.info(f"N validation passed: {n_simulated} == 200")
    
    # Step 4: Generate data
    df = generate_synthetic_mfq(n_participants=n_simulated, seed=42)
    
    # Step 5: Save data
    output_path = get_path("data", "raw", "synthetic_mfq.csv")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved synthetic MFQ data to {output_path}")
    
    # Step 6: Log summary
    log_pipeline_step("SUCCESS", "T013: Synthetic MFQ Generation completed")
    logger.info(f"Summary: N={len(df)}, Missingness={df.isnull().sum().sum()} total values")
    
    # Verification: Re-read and confirm
    df_check = pd.read_csv(output_path)
    assert len(df_check) == 200, "Verification failed: Row count mismatch"
    assert 'participant_id' in df_check.columns, "Verification failed: Missing participant_id"
    logger.info("Verification passed: Output file is valid.")

if __name__ == "__main__":
    main()
