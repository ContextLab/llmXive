"""
Synthetic data generator for verification mode.
Implements T008.
"""
import os
import logging
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

def generate_synthetic_subject_data(n_subjects: int, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate synthetic subject data.
    Ensures at least 50 musicians and 50 non-musicians if n_subjects >= 100.
    For small n (verification tests), generates a balanced mix.
    """
    if seed is not None:
        np.random.seed(seed)
    
    # Ensure at least some of each group
    n_musician = n_subjects // 2
    n_non_musician = n_subjects - n_musician
    
    data = {
        'subject_id': [f'SUBJ-{i:04d}' for i in range(n_subjects)],
        'group': ['musician'] * n_musician + ['non_musician'] * n_non_musician,
        'years_of_training': [],
        'age': [],
        'sex': [],
        'motion_score': [],
        'ses_score': []
    }
    
    # Musicians: years >= 1 (mostly), age 10-25
    for _ in range(n_musician):
        data['years_of_training'].append(np.random.uniform(1.0, 15.0))
        data['age'].append(np.random.uniform(10, 25))
        data['sex'].append(np.random.choice(['M', 'F']))
        data['motion_score'].append(np.random.uniform(0.05, 0.3))
        data['ses_score'].append(np.random.uniform(1, 10))
    
    # Non-musicians: years < 1 (mostly), age 10-25
    for _ in range(n_non_musician):
        # Some might be >= 1, but most < 1 to test filtering
        val = np.random.uniform(0, 2.0)
        # Ensure some are < 1 to test T015 filter
        if np.random.random() > 0.5:
            val = np.random.uniform(0, 0.9)
        data['years_of_training'].append(val)
        data['age'].append(np.random.uniform(10, 25))
        data['sex'].append(np.random.choice(['M', 'F']))
        data['motion_score'].append(np.random.uniform(0.05, 0.3))
        data['ses_score'].append(np.random.uniform(1, 10))
    
    return pd.DataFrame(data)

def generate_synthetic_connectivity_matrix(n_rois: int = 100, seed: Optional[int] = None) -> np.ndarray:
    """Generate a random symmetric correlation matrix."""
    if seed is not None:
        np.random.seed(seed)
    
    # Random matrix
    A = np.random.randn(n_rois, n_rois)
    # Make symmetric
    M = (A + A.T) / 2
    # Normalize to [-1, 1] (approx correlation)
    # Simple approach: use correlation of random vectors
    data = np.random.randn(n_rois, 50) # 50 time points
    corr = np.corrcoef(data)
    corr = np.nan_to_num(corr, nan=0.0)
    return corr

def generate_synthetic_dataset(n_subjects: int = 10, seed: Optional[int] = None) -> pd.DataFrame:
    """
    Generate a full synthetic dataset for verification.
    """
    return generate_synthetic_subject_data(n_subjects, seed)

def main():
    """Generate a sample dataset."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=10)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    
    df = generate_synthetic_dataset(args.n, args.seed)
    print(df.head())
    return df

if __name__ == "__main__":
    main()
