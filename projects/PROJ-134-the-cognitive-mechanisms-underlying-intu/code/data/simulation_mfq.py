import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import ensure_directories, init_random_seeds
from code.utils.logging_utils import log_pipeline_step
from code.utils.norms import get_covariance_matrix, validate_against_norms
from code.analysis.power_analysis import validate_ground_truth_effect

LOG_FILE = "data/logs/simulation_mfq_log.txt"
OUTPUT_FILE = "data/processed/synthetic_mfq.csv"

# Gervais et al. (2011) approximate means and standard deviations for Moral Foundations
# Care, Fairness, Loyalty, Authority, Purity
MEANS = [4.2, 4.0, 3.8, 3.5, 3.2]
STDS = [1.1, 1.2, 1.3, 1.4, 1.5]

# Configuration for simulation
N_PARTICIPANTS = 500
# Ground truth effect size for salience manipulation (standardized difference)
# This is used to validate against MDES from T045
GROUND_TRUTH_EFFECT = 0.5 

def generate_covariance_matrix(n_features: int = 5) -> np.ndarray:
    """
    Generate a positive semi-definite covariance matrix for the 5 moral foundations.
    Uses the covariance structure derived from norms in code/utils/norms.py
    to ensure consistency with Gervais et al. data.
    """
    init_random_seeds()
    # Use the robust covariance generation from norms module
    # This ensures the simulated data aligns with the psychometric norms
    cov_matrix = get_covariance_matrix()
    
    # Ensure matrix is positive semi-definite (numerical stability)
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)
    eigenvalues = np.maximum(eigenvalues, 1e-8)
    cov_matrix = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    
    return cov_matrix

def generate_synthetic_mfq(n_participants: int = N_PARTICIPANTS) -> pd.DataFrame:
    """
    Generate synthetic MFQ data based on Gervais et al. (2011) multivariate normal distributions.
    
    Validation:
    1. Validates ground_truth_effect against MDES (T045) before generation
    2. Validates generated distribution against norms after generation
    
    Returns:
        pd.DataFrame: Synthetic MFQ data with columns:
            participant_id, care, fairness, loyalty, authority, purity
    """
    init_random_seeds()
    log_pipeline_step("Starting MFQ generation with MDES validation", LOG_FILE)
    
    # Validate ground truth effect against MDES (T045 requirement)
    # This ensures our simulation is statistically powered
    is_valid = validate_ground_truth_effect(GROUND_TRUTH_EFFECT)
    if not is_valid:
        log_pipeline_step(f"Ground truth effect {GROUND_TRUTH_EFFECT} is below MDES threshold", LOG_FILE)
        raise ValueError(f"Ground truth effect {GROUND_TRUTH_EFFECT} is below MDES threshold. "
                       f"Adjust simulation parameters or increase sample size.")
    
    log_pipeline_step(f"Ground truth effect {GROUND_TRUTH_EFFECT} validated against MDES", LOG_FILE)
    
    cov_matrix = generate_covariance_matrix()
    
    # Generate multivariate normal data
    data = np.random.multivariate_normal(MEANS, cov_matrix, n_participants)
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=['care', 'fairness', 'loyalty', 'authority', 'purity'])
    
    # Add participant IDs
    df['participant_id'] = range(1, n_participants + 1)
    
    # Clip values to plausible range [1, 7] for Likert scale
    for col in ['care', 'fairness', 'loyalty', 'authority', 'purity']:
        df[col] = df[col].clip(1, 7)
    
    # Reorder columns
    df = df[['participant_id', 'care', 'fairness', 'loyalty', 'authority', 'purity']]
    
    # Validate against norms (T017 requirement)
    validation_result = validate_against_norms(df)
    if not validation_result['is_valid']:
        log_pipeline_step(f"WARNING: Generated data deviates from norms: {validation_result['message']}", LOG_FILE)
    else:
        log_pipeline_step(f"Generated data validated against norms: {validation_result['message']}", LOG_FILE)
    
    log_pipeline_step(f"Generated MFQ data with shape: {df.shape}", LOG_FILE)
    return df

def main():
    """Main entry point for MFQ simulation (T013)."""
    log_pipeline_step("Starting MFQ Simulation (T013)", LOG_FILE)
    
    ensure_directories()
    
    output_path = project_root / OUTPUT_FILE
    
    try:
        # Generate synthetic data
        df = generate_synthetic_mfq(N_PARTICIPANTS)
        
        # Save to disk
        df.to_csv(output_path, index=False)
        
        log_pipeline_step(f"MFQ data saved to {output_path}", LOG_FILE)
        log_pipeline_step(f"MFQ Simulation (T013) completed successfully", LOG_FILE)
        
        print(f"Successfully generated synthetic MFQ data: {output_path}")
        print(f"Shape: {df.shape}")
        print(f"Ground truth effect used: {GROUND_TRUTH_EFFECT}")
        
        # Return success
        return True
        
    except Exception as e:
        log_pipeline_step(f"MFQ Simulation (T013) failed: {str(e)}", LOG_FILE)
        print(f"Error generating MFQ data: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)