from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

from .logging import get_logger
from .chemical_families import assign_chemical_family

logger = get_logger(__name__)


def get_chemical_family(element: str) -> str:
    """Get the chemical family for an element."""
    return assign_chemical_family(element)


def sample_by_chemical_family(
    df: pd.DataFrame,
    target_rows: int,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Perform stratified sampling by chemical family.

    Args:
        df: Input DataFrame with a 'dominant_element' column
        target_rows: Target number of rows in the sample
        random_state: Random seed for reproducibility

    Returns:
        Sampled DataFrame
    """
    df = df.copy()
    df["chem_family"] = df["dominant_element"].apply(assign_chemical_family)

    # Calculate sampling fractions
    total = len(df)
    if total <= target_rows:
        return df

    fractions = {
        family: count / total
        for family, count in df["chem_family"].value_counts().items()
    }

    # Sample
    sampled = df.groupby("chem_family", group_keys=False).apply(
        lambda x: x.sample(
            n=max(1, int(len(x) * target_rows / total)), random_state=random_state
        )
    )

    logger.info(
        f"Sampled {len(sampled)} rows from {total} by chemical family"
    )
    return sampled.reset_index(drop=True)
