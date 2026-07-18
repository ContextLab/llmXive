"""
Quality Control module for RNA-seq data.

Implements checks for sample coverage, replicates, and metadata completeness.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger("qc")

def check_sample_coverage(
    tpm_df: pd.DataFrame,
    threshold: float = 1000.0
) -> pd.DataFrame:
    """
    Checks the total TPM coverage for each sample.
    
    Args:
        tpm_df: DataFrame of TPM values.
        threshold: Minimum total TPM required per sample.
        
    Returns:
        DataFrame with coverage statistics.
    """
    coverage = tpm_df.sum(axis=0)
    stats = pd.DataFrame({
        "total_tpm": coverage,
        "num_genes_detected": (tpm_df > 0).sum(axis=0),
        "mean_tpm": tpm_df.mean(axis=0),
        "median_tpm": tpm_df.median(axis=0)
    })
    
    stats["is_low_coverage"] = stats["total_tpm"] < threshold
    
    logger.info(f"Sample coverage check completed. {stats['is_low_coverage'].sum()} low coverage samples.")
    return stats

def flag_low_coverage_samples(
    coverage_stats: pd.DataFrame
) -> List[str]:
    """
    Returns a list of sample names that are flagged as low coverage.
    
    Args:
        coverage_stats: DataFrame from check_sample_coverage.
        
    Returns:
        List of sample names.
    """
    return coverage_stats[coverage_stats["is_low_coverage"]].index.tolist()

def check_replicates(
    metadata_df: pd.DataFrame,
    group_column: str,
    min_replicates: int = 2
) -> Tuple[bool, List[str]]:
    """
    Checks if each group has at least min_replicates.
    
    Args:
        metadata_df: DataFrame containing sample metadata.
        group_column: Column name for grouping (e.g., 'tissue', 'treatment').
        min_replicates: Minimum number of replicates required.
        
    Returns:
        Tuple of (is_valid, list of groups with insufficient replicates).
    """
    group_counts = metadata_df[group_column].value_counts()
    insufficient_groups = group_counts[group_counts < min_replicates].index.tolist()
    
    is_valid = len(insufficient_groups) == 0
    
    if not is_valid:
        logger.warning(f"Groups with insufficient replicates: {insufficient_groups}")
    
    return is_valid, insufficient_groups

def check_metadata_completeness(
    metadata_df: pd.DataFrame,
    required_columns: List[str]
) -> Tuple[bool, List[str]]:
    """
    Checks if all required metadata columns are present and non-empty.
    
    Args:
        metadata_df: Metadata DataFrame.
        required_columns: List of required column names.
        
    Returns:
        Tuple of (is_valid, list of missing/empty columns).
    """
    missing_columns = []
    for col in required_columns:
        if col not in metadata_df.columns:
            missing_columns.append(f"Missing column: {col}")
        elif metadata_df[col].isna().all():
            missing_columns.append(f"Empty column: {col}")
    
    return len(missing_columns) == 0, missing_columns