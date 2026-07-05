"""
Dataset sampling utility for the Brain Network Efficiency and Fluid Intelligence project.

Provides functions to sample subjects from a dataset while maintaining
statistical properties and respecting the ≤500 subjects constraint.
"""
import random
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from .logging import get_logger

logger = get_logger(__name__)


def sample_subjects(
    subjects: List[Dict[str, Any]],
    max_subjects: int = 500,
    seed: Optional[int] = None,
    stratify_by: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Sample a subset of subjects from the dataset.

    Args:
        subjects: List of subject dictionaries
        max_subjects: Maximum number of subjects to return (default: 500)
        seed: Random seed for reproducibility
        stratify_by: Optional column name to stratify sampling by

    Returns:
        A sampled list of subjects
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    original_count = len(subjects)
    if original_count <= max_subjects:
        logger.info(f"Dataset has {original_count} subjects (≤ {max_subjects}). No sampling required.")
        return subjects

    logger.info(f"Sampling subjects: {original_count} -> {max_subjects} (seed={seed})")

    if stratify_by and all(stratify_by in s for s in subjects):
        # Stratified sampling
        groups = {}
        for subject in subjects:
            key = subject[stratify_by]
            if key not in groups:
                groups[key] = []
            groups[key].append(subject)

        sampled_subjects = []
        for key, group in groups.items():
            group_size = len(group)
            # Calculate proportional sample size
            sample_size = int((group_size / original_count) * max_subjects)
            # Ensure at least one subject per group if possible
            sample_size = max(1, sample_size)
            
            # Adjust to not exceed max_subjects (handle rounding errors)
            remaining_slots = max_subjects - len(sampled_subjects)
            if remaining_slots <= 0:
                break
            sample_size = min(sample_size, remaining_slots)

            sampled = random.sample(group, min(sample_size, len(group)))
            sampled_subjects.extend(sampled)
        
        # If we still have slots and haven't hit max, fill with random from remaining
        if len(sampled_subjects) < max_subjects:
            remaining_subjects = [s for s in subjects if s not in sampled_subjects]
            fill_count = min(max_subjects - len(sampled_subjects), len(remaining_subjects))
            if fill_count > 0:
                sampled_subjects.extend(random.sample(remaining_subjects, fill_count))

        logger.info(f"Stratified sampling complete. Groups: {list(groups.keys())}")
        return sampled_subjects
    else:
        # Random sampling
        sampled = random.sample(subjects, min(max_subjects, len(subjects)))
        logger.info(f"Random sampling complete.")
        return sampled


def sample_dataframe(
    df: pd.DataFrame,
    max_rows: int = 500,
    seed: Optional[int] = None,
    stratify_by: Optional[str] = None
) -> pd.DataFrame:
    """
    Sample a subset of rows from a DataFrame.

    Args:
        df: Input DataFrame
        max_rows: Maximum number of rows to return (default: 500)
        seed: Random seed for reproducibility
        stratify_by: Optional column name to stratify sampling by

    Returns:
        A sampled DataFrame
    """
    if seed is not None:
        np.random.seed(seed)

    original_count = len(df)
    if original_count <= max_rows:
        logger.info(f"DataFrame has {original_count} rows (≤ {max_rows}). No sampling required.")
        return df

    logger.info(f"Sampling DataFrame: {original_count} -> {max_rows} (seed={seed})")

    if stratify_by and stratify_by in df.columns:
        # Stratified sampling using pandas
        # Calculate sample size per group
        group_counts = df[stratify_by].value_counts()
        sample_sizes = (group_counts / original_count * max_rows).astype(int)
        # Ensure at least 1 per group
        sample_sizes = sample_sizes.clip(lower=1)
        
        # Adjust for rounding errors to ensure we don't exceed max_rows
        total_sample = sample_sizes.sum()
        if total_sample > max_rows:
            diff = total_sample - max_rows
            # Reduce from largest groups
            for idx in sample_sizes.sort_values(ascending=False).index:
                if diff <= 0:
                    break
                reduce_by = min(diff, sample_sizes[idx] - 1)
                sample_sizes[idx] -= reduce_by
                diff -= reduce_by

        sampled_dfs = []
        for group_val, n in sample_sizes.items():
            group_df = df[df[stratify_by] == group_val]
            sampled_dfs.append(group_df.sample(n=min(n, len(group_df)), random_state=seed))
        
        result = pd.concat(sampled_dfs, ignore_index=True)
        logger.info(f"Stratified sampling complete. Groups: {list(group_counts.index)}")
        return result
    else:
        # Random sampling
        result = df.sample(n=min(max_rows, len(df)), random_state=seed)
        logger.info(f"Random sampling complete.")
        return result