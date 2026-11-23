"""
Sampling utilities for dataset management.

Provides functions for sampling subjects from datasets while maintaining
reproducibility and respecting project constraints.
"""
import random
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from .logging import get_logger
from config import RANDOM_SEED

logger = get_logger(__name__)


def sample_subjects(
    subject_ids: List[str],
    max_subjects: int = 500,
    random_seed: Optional[int] = None
) -> List[str]:
    """
    Sample a subset of subject IDs.

    Args:
        subject_ids: List of all subject IDs
        max_subjects: Maximum number of subjects to sample (default 500)
        random_seed: Random seed for reproducibility (default uses config value)

    Returns:
        List of sampled subject IDs
    """
    if random_seed is None:
        random_seed = RANDOM_SEED

    random.seed(random_seed)
    np.random.seed(random_seed)

    if len(subject_ids) <= max_subjects:
        logger.info(f"All {len(subject_ids)} subjects retained (≤ {max_subjects})")
        return subject_ids

    sampled = random.sample(subject_ids, max_subjects)
    logger.info(f"Sampled {max_subjects} subjects from {len(subject_ids)} total")
    return sampled


def sample_dataframe(
    df: pd.DataFrame,
    max_subjects: int = 500,
    subject_column: str = "subject_id",
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Sample a DataFrame to a maximum number of subjects.

    Args:
        df: Input DataFrame
        max_subjects: Maximum number of subjects (default 500)
        subject_column: Name of the subject ID column
        random_seed: Random seed for reproducibility

    Returns:
        Sampled DataFrame
    """
    if random_seed is None:
        random_seed = RANDOM_SEED

    np.random.seed(random_seed)

    unique_subjects = df[subject_column].unique()

    if len(unique_subjects) <= max_subjects:
        logger.info(f"All {len(unique_subjects)} subjects retained in DataFrame")
        return df

    sampled_subjects = np.random.choice(unique_subjects, size=max_subjects, replace=False)
    sampled_df = df[df[subject_column].isin(sampled_subjects)]

    logger.info(
        f"Sampled {max_subjects} subjects from {len(unique_subjects)} total "
        f"in DataFrame ({len(sampled_df)} rows)"
    )

    return sampled_df
