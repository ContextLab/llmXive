"""
Synthetic data generator for Verification Mode only.

CRITICAL: This module generates SIMULATED data for code verification and
null-hypothesis testing. It must NOT be used in Analysis Mode with real
biological data.

The generator creates a 'Null-First' dataset where no injected effects exist
between musical training and functional connectivity, allowing validation
of the statistical pipeline's ability to correctly identify null results.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit, get_current_memory_mb

logger = get_logger(__name__)

# Constants for synthetic generation
DEFAULT_N_SUBJECTS = 200
DEFAULT_N_ROIS = 90  # AAL atlas standard
RANDOM_SEED = 42

# Demographic parameters
AGE_MEAN = 16.0
AGE_STD = 1.5
MOTION_MEAN = 0.2
MOTION_STD = 0.1
SES_MEAN = 50.0
SES_STD = 15.0

# Training distribution parameters
MUSICIAN_PROB = 0.5
TRAINING_YEARS_MEAN_MUSICIAN = 5.0
TRAINING_YEARS_STD_MUSICIAN = 3.0
TRAINING_YEARS_MEAN_NON_MUSICIAN = 0.5
TRAINING_YEARS_STD_NON_MUSICIAN = 0.5

# Connectivity parameters (NULL HYPOTHESIS: No effect of group)
BASE_CORRELATION_MEAN = 0.0
BASE_CORRELATION_STD = 0.5


def generate_synthetic_subject_data(
    n_subjects: int = DEFAULT_N_SUBJECTS,
    random_seed: int = RANDOM_SEED
) -> pd.DataFrame:
    """
    Generate synthetic subject demographic and training data.
    
    Args:
        n_subjects: Number of subjects to generate
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with subject metadata
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds limit during generation
    """
    check_memory_limit()
    rng = np.random.default_rng(random_seed)
    
    # Generate group assignments
    groups = rng.choice(['musician', 'non_musician'], size=n_subjects, p=[MUSICIAN_PROB, 1-MUSICIAN_PROB])
    
    # Generate years of training based on group (NULL: distributions overlap significantly)
    years_training = np.zeros(n_subjects)
    musician_mask = groups == 'musician'
    non_musician_mask = groups == 'non_musician'
    
    # Musician training years (truncated at 0)
    musician_years = rng.normal(
        TRAINING_YEARS_MEAN_MUSICIAN, 
        TRAINING_YEARS_STD_MUSICIAN, 
        size=musician_mask.sum()
    )
    musician_years = np.maximum(0, musician_years)
    
    # Non-musician training years (truncated at 0, mostly low)
    non_musician_years = rng.normal(
        TRAINING_YEARS_MEAN_NON_MUSICIAN,
        TRAINING_YEARS_STD_NON_MUSICIAN,
        size=non_musician_mask.sum()
    )
    non_musician_years = np.maximum(0, non_musician_years)
    
    years_training[musician_mask] = musician_years
    years_training[non_musician_mask] = non_musician_years
    
    # Generate demographics (independent of group for NULL hypothesis)
    age = rng.normal(AGE_MEAN, AGE_STD, n_subjects)
    age = np.clip(age, 12, 20)  # Adolescent range
    
    sex = rng.choice(['M', 'F'], size=n_subjects)
    
    motion_score = rng.normal(MOTION_MEAN, MOTION_STD, n_subjects)
    motion_score = np.clip(motion_score, 0, 1)
    
    ses_score = rng.normal(SES_MEAN, SES_STD, n_subjects)
    ses_score = np.clip(ses_score, 0, 100)
    
    # Generate subject IDs
    subject_ids = [f"SUBJ_{i:04d}" for i in range(n_subjects)]
    
    df = pd.DataFrame({
        'subject_id': subject_ids,
        'group': groups,
        'years_of_training': years_training,
        'age': age,
        'sex': sex,
        'motion_score': motion_score,
        'ses_score': ses_score
    })
    
    logger.info(f"Generated {n_subjects} synthetic subjects: "
               f"{sum(musician_mask)} musicians, {sum(non_musician_mask)} non-musicians")
    
    return df


def generate_synthetic_connectivity_matrix(
    n_rois: int = DEFAULT_N_ROIS,
    random_seed: int = RANDOM_SEED,
    group: str = 'musician'
) -> np.ndarray:
    """
    Generate a synthetic functional connectivity matrix.
    
    CRITICAL: This generates NULL data with NO group-specific effects.
    The correlation structure is random and independent of the group label.
    
    Args:
        n_rois: Number of ROIs (brain regions)
        random_seed: Random seed for reproducibility
        group: Group label (unused in NULL generation, but kept for API consistency)
        
    Returns:
        2D numpy array representing the connectivity matrix (n_rois x n_rois)
    """
    check_memory_limit()
    rng = np.random.default_rng(random_seed)
    
    # Generate random correlation matrix
    # Start with random data
    data = rng.normal(0, 1, size=(n_rois, 1000))  # 1000 timepoints
    
    # Compute correlation matrix
    corr_matrix = np.corrcoef(data)
    
    # Ensure symmetry and set diagonal to 1
    corr_matrix = (corr_matrix + corr_matrix.T) / 2
    np.fill_diagonal(corr_matrix, 1.0)
    
    # Clip to valid correlation range
    corr_matrix = np.clip(corr_matrix, -1, 1)
    
    return corr_matrix


def generate_synthetic_dataset(
    n_subjects: int = DEFAULT_N_SUBJECTS,
    n_rois: int = DEFAULT_N_ROIS,
    output_dir: Optional[str] = None,
    random_seed: int = RANDOM_SEED,
    save_matrices: bool = False
) -> Tuple[pd.DataFrame, Optional[Dict[str, np.ndarray]]]:
    """
    Generate a complete synthetic dataset for verification mode.
    
    This function generates:
    1. Subject metadata DataFrame
    2. Optional connectivity matrices for each subject
    
    IMPORTANT: This is SIMULATION MODE ONLY. The data contains NO injected
    effects between musical training and connectivity (Null Hypothesis).
    
    Args:
        n_subjects: Number of subjects to generate
        n_rois: Number of ROIs per connectivity matrix
        output_dir: Directory to save generated data (optional)
        random_seed: Random seed for reproducibility
        save_matrices: Whether to save connectivity matrices to disk
        
    Returns:
        Tuple of (subject_df, connectivity_dict) where connectivity_dict
        maps subject_id -> connectivity matrix (or None if not saved)
        
    Raises:
        MemoryLimitExceeded: If memory usage exceeds limit
        ValueError: If parameters are invalid
    """
    logger.info(f"Starting synthetic dataset generation: {n_subjects} subjects, "
               f"{n_rois} ROIs, seed={random_seed}")
    
    # Check memory before generation
    check_memory_limit()
    
    rng = np.random.default_rng(random_seed)
    
    # Generate subject data
    subject_df = generate_synthetic_subject_data(n_subjects, random_seed)
    
    connectivity_dict = {}
    
    if save_matrices and output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for idx, row in subject_df.iterrows():
            # Check memory periodically
            if idx % 10 == 0:
                check_memory_limit()
            
            # Generate connectivity matrix with unique seed per subject
            subj_seed = int(rng.integers(0, 2**31))
            matrix = generate_synthetic_connectivity_matrix(
                n_rois=n_rois,
                random_seed=subj_seed,
                group=row['group']
            )
            
            connectivity_dict[row['subject_id']] = matrix
            
            # Save matrix if requested
            matrix_path = output_path / f"connectivity_{row['subject_id']}.npy"
            np.save(str(matrix_path), matrix)
            
            logger.debug(f"Generated connectivity for {row['subject_id']}")
    
    # Final memory check
    check_memory_limit()
    
    logger.info("Synthetic dataset generation complete")
    return subject_df, connectivity_dict if save_matrices else None


def main():
    """
    Main entry point for standalone execution.
    Generates a synthetic dataset and saves it to data/raw/.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate synthetic fMRI dataset for verification")
    parser.add_argument("--n-subjects", type=int, default=DEFAULT_N_SUBJECTS,
                      help="Number of subjects to generate")
    parser.add_argument("--n-rois", type=int, default=DEFAULT_N_ROIS,
                      help="Number of ROIs per connectivity matrix")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED,
                      help="Random seed")
    parser.add_argument("--output-dir", type=str, default="data/raw",
                      help="Output directory for generated data")
    parser.add_argument("--save-matrices", action="store_true",
                      help="Save individual connectivity matrices")
    
    args = parser.parse_args()
    
    logger.info("Running synthetic generator in standalone mode")
    
    # Ensure output directory exists
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate dataset
    subject_df, matrices = generate_synthetic_dataset(
        n_subjects=args.n_subjects,
        n_rois=args.n_rois,
        output_dir=args.output_dir if args.save_matrices else None,
        random_seed=args.seed,
        save_matrices=args.save_matrices
    )
    
    # Save subject data
    subject_csv_path = output_path / "subjects_raw.csv"
    subject_df.to_csv(subject_csv_path, index=False)
    logger.info(f"Saved subject data to {subject_csv_path}")
    
    if args.save_matrices and matrices:
        logger.info(f"Saved {len(matrices)} connectivity matrices to {args.output_dir}")
    
    logger.info("Synthetic generation complete")
    
    # Print summary
    print(f"\nSynthetic Dataset Summary:")
    print(f"  Total subjects: {len(subject_df)}")
    print(f"  Musicians: {len(subject_df[subject_df['group'] == 'musician'])}")
    print(f"  Non-musicians: {len(subject_df[subject_df['group'] == 'non_musician'])}")
    print(f"  ROIs per matrix: {args.n_rois}")
    print(f"  Output directory: {args.output_dir}")
    print(f"  Note: This is NULL data with NO injected effects.")


if __name__ == "__main__":
    main()