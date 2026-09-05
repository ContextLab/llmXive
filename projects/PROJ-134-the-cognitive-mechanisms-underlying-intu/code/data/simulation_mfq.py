"""
Synthetic MFQ data generation based on Gervais et al. multivariate normal distributions.
"""
from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from code.config import get_path, load_yaml_config
from code.analysis.power_analysis import load_mdes_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path("data/logs/simulation_mfq.log"))
    ]
)
logger = logging.getLogger(__name__)

OUTPUT_PATH = "data/raw/synthetic_mfq.csv"
NORMS_PATH = "data/config/gervais_norms.yaml"


def load_mdes_report() -> dict:
    """Load the MDES report to validate parameters."""
    report_path = get_path("state/mdes_report.yaml")
    if not report_path.exists():
        raise FileNotFoundError(
            f"MDES report missing at {report_path}. Ensure T045 (Power Analysis) is complete before running this task."
        )
    
    import yaml
    with open(report_path, 'r') as f:
        return yaml.safe_load(f)


def validate_ground_truth_effect(effect_size: float, mdes_report: dict) -> bool:
    """Validate that the ground truth effect is within reasonable bounds."""
    mdes_value = mdes_report.get('mdes_value', 0)
    if effect_size < mdes_value * 0.5:
        logger.warning(f"Effect size {effect_size} is below 50% of MDES ({mdes_value})")
    return True


def get_correlation_matrix() -> np.ndarray:
    """
    Return the correlation matrix for MFQ dimensions based on literature.
    Typical correlations between foundations range from 0.3 to 0.6.
    """
    # 5 foundations: Care, Fairness, Loyalty, Authority, Purity
    corr = np.array([
        [1.0, 0.5, 0.3, 0.3, 0.3],
        [0.5, 1.0, 0.3, 0.3, 0.3],
        [0.3, 0.3, 1.0, 0.5, 0.4],
        [0.3, 0.3, 0.5, 1.0, 0.4],
        [0.3, 0.3, 0.4, 0.4, 1.0]
    ])
    return corr


def generate_covariance_matrix(means: list, stds: list, corr_matrix: np.ndarray) -> np.ndarray:
    """Generate covariance matrix from means, stds, and correlation matrix."""
    stds_arr = np.array(stds)
    cov = np.outer(stds_arr, stds_arr) * corr_matrix
    return cov


def generate_synthetic_mfq(n_participants: int, norms: dict, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic MFQ data based on Gervais et al. norms.
    
    Args:
        n_participants: Number of participants to simulate
        norms: Dictionary of mean and std for each foundation
        seed: Random seed for reproducibility
        
    Returns:
        DataFrame with synthetic MFQ data
    """
    np.random.seed(seed)
    
    foundations = ['care', 'fairness', 'loyalty', 'authority', 'purity']
    means = [norms[f]['mean'] for f in foundations]
    stds = [norms[f]['std'] for f in foundations]
    
    corr_matrix = get_correlation_matrix()
    cov_matrix = generate_covariance_matrix(means, stds, corr_matrix)
    
    # Generate multivariate normal data
    data = np.random.multivariate_normal(means, cov_matrix, size=n_participants)
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=foundations)
    df['participant_id'] = range(1, n_participants + 1)
    
    # Calculate total score
    df['total_score'] = df[foundations].sum(axis=1)
    
    # Reorder columns
    df = df[['participant_id'] + foundations + ['total_score']]
    
    return df


def main() -> None:
    """Main entry point for MFQ simulation."""
    try:
        logger.info("Starting synthetic MFQ generation")
        
        # Load MDES report to get sample size
        mdes_report = load_mdes_report()
        n_participants = mdes_report.get('n_participants', 200)
        
        # Load norms
        norms_config = load_yaml_config(NORMS_PATH)
        
        # Validate ground truth effect if present
        if 'ground_truth_effect' in mdes_report:
            validate_ground_truth_effect(mdes_report['ground_truth_effect'], mdes_report)
        
        # Generate data
        df = generate_synthetic_mfq(n_participants, norms_config)
        
        # Save to disk
        full_path = get_path(OUTPUT_PATH)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving synthetic MFQ data to {full_path}")
        df.to_csv(full_path, index=False)
        
        logger.info(f"Generated {len(df)} synthetic MFQ records")
        
    except Exception as e:
        logger.error(f"MFQ simulation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
