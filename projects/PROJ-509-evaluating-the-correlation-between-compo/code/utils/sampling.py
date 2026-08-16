"""
Sampling utilities for stratified sampling by chemical family.
"""
from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

from .logging import get_logger
from .chemical_families import assign_chemical_family


logger = get_logger(__name__)


def get_chemical_family(row: pd.Series, element_column: str = "dominant_element") -> str:
    """
    Get the chemical family for a row based on its dominant element.

    Args:
        row: A pandas Series representing a row in the DataFrame.
        element_column: The column name containing the dominant element.

    Returns:
        The chemical family string.
    """
    element = row.get(element_column, "")
    if pd.isna(element) or not isinstance(element, str):
        return "Unknown"
    return assign_chemical_family(element.strip())


def sample_by_chemical_family(
    df: pd.DataFrame,
    target_rows: int,
    random_state: int = 42,
    element_column: str = "dominant_element"
) -> pd.DataFrame:
    """
    Perform stratified sampling by chemical family.

    Args:
        df: The input DataFrame.
        target_rows: The target number of rows in the sample.
        random_state: The random seed for reproducibility.
        element_column: The column name containing the dominant element.

    Returns:
        The sampled DataFrame.
    """
    np.random.seed(random_state)

    # Assign chemical families
    df = df.copy()
    df["_chemical_family"] = df.apply(lambda row: get_chemical_family(row, element_column), axis=1)

    # Calculate sampling fractions
    family_counts = df["_chemical_family"].value_counts()
    total_rows = len(df)

    if target_rows >= total_rows:
        logger.info(f"Target rows ({target_rows}) >= total rows ({total_rows}). Returning full dataset.")
        return df.drop(columns=["_chemical_family"])

    # Calculate proportional sampling
    sampling_ratio = target_rows / total_rows
    logger.info(f"Sampling ratio: {sampling_ratio:.2%} ({target_rows}/{total_rows})")

    # Sample from each family
    sampled_dfs = []
    for family, count in family_counts.items():
        n_sample = max(1, int(count * sampling_ratio))
        family_df = df[df["_chemical_family"] == family]
        sampled = family_df.sample(n=min(n_sample, count), random_state=random_state)
        sampled_dfs.append(sampled)
        logger.debug(f"Sampled {len(sampled)} rows from family {family} (total: {count})")

    # Combine and clean up
    sampled_df = pd.concat(sampled_dfs, ignore_index=True)
    sampled_df = sampled_df.drop(columns=["_chemical_family"])

    logger.info(f"Final sample size: {len(sampled_df)} rows")
    return sampled_df
