"""
Diversity analysis module.
Implements rarefaction and alpha-diversity calculations.
"""
import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def rarefy_table(counts: pd.DataFrame, depth: int) -> pd.DataFrame:
    """
    Rarefy OTU table to a fixed sequencing depth.

    Args:
        counts: DataFrame of OTU counts (rows= samples, cols= OTUs).
        depth: Target sequencing depth.

    Returns:
        Rarefied DataFrame.
    """
    if depth <= 0:
        raise ValueError("Depth must be positive")

    rarefied = pd.DataFrame(index=counts.index, columns=counts.columns, dtype=int)

    for idx in counts.index:
        total = counts.loc[idx].sum()
        if total < depth:
            # If sample has less than depth, keep as is or skip?
            # For this implementation, we keep as is but log warning
            logger.warning(f"Sample {idx} has total count {total} < depth {depth}. Skipping rarefaction.")
            rarefied.loc[idx] = counts.loc[idx]
        else:
            # Multinomial sampling
            probs = counts.loc[idx] / total
            rarefied.loc[idx] = np.random.multinomial(depth, probs.values)

    return rarefied

def calculate_alpha_diversity(counts: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics (Shannon, Simpson, Observed OTUs).

    Args:
        counts: DataFrame of OTU counts.

    Returns:
        DataFrame with diversity metrics per sample.
    """
    results = []

    for idx in counts.index:
        row = counts.loc[idx]
        row = row[row > 0]  # Remove zeros for log calculations

        total = row.sum()
        if total == 0:
            shannon = 0.0
            simpson = 0.0
            observed = 0
        else:
            p = row / total
            shannon = -np.sum(p * np.log(p))
            simpson = 1 - np.sum(p ** 2)
            observed = len(row)

        results.append({
            "sample_id": idx,
            "shannon_diversity": shannon,
            "simpson_diversity": simpson,
            "observed_otus": observed
        })

    return pd.DataFrame(results)

def main():
    """CLI entry point for diversity analysis."""
    logger.info("Diversity analysis module loaded.")

if __name__ == "__main__":
    from src.logging_config import configure_root_logger
    configure_root_logger()
    main()
