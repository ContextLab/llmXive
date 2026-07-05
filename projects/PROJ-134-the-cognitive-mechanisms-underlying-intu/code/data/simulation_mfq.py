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

LOG_FILE = "data/logs/simulation_mfq_log.txt"
OUTPUT_FILE = "data/processed/synthetic_mfq.csv"

# Gervais et al. (2011) approximate means and standard deviations for Moral Foundations
# Care, Fair, Loyalty, Authority, Purity
MEANS = [4.2, 4.0, 3.8, 3.5, 3.2]
STDS = [1.1, 1.2, 1.3, 1.4, 1.5]

def generate_covariance_matrix(n_features: int = 5) -> np.ndarray:
    """
    Generate a positive semi-definite covariance matrix for the 5 moral foundations.
    Uses a simple correlation structure with moderate positive correlations.
    """
    np.random.seed(42)
    # Generate random matrix
    A = np.random.rand(n_features, n_features)
    # Make it symmetric and positive semi-definite
    cov = np.dot(A, A.T)
    # Scale to reasonable variances (squared stds)
    stds = np.array(STDS)
    cov = cov * np.outer(stds, stds) / np.max(cov) * np.var(stds)
    # Ensure diagonal is correct
    np.fill_diagonal(cov, stds ** 2)
    return cov

def generate_synthetic_mfq(n_participants: int = 500) -> pd.DataFrame:
    """
    Generate synthetic MFQ data based on Gervais et al. (2011) distributions.
    Returns a DataFrame with columns: participant_id, care, fairness, loyalty, authority, purity
    """
    init_random_seeds()
    log_pipeline_step(f"Generating synthetic MFQ data for {n_participants} participants", LOG_FILE)
    
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
    
    log_pipeline_step(f"Generated MFQ data with shape: {df.shape}", LOG_FILE)
    return df

def main():
    """Main entry point for MFQ simulation."""
    log_pipeline_step("Starting MFQ Simulation (T013)", LOG_FILE)
    
    ensure_directories()
    
    n_participants = 500
    output_path = project_root / OUTPUT_FILE
    
    try:
        df = generate_synthetic_mfq(n_participants)
        df.to_csv(output_path, index=False)
        log_pipeline_step(f"MFQ data saved to {output_path}", LOG_FILE)
        print(f"Successfully generated synthetic MFQ data: {output_path}")
        print(f"Shape: {df.shape}")
        return True
    except Exception as e:
        log_pipeline_step(f"MFQ Simulation failed: {str(e)}", LOG_FILE)
        print(f"Error generating MFQ data: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
