"""
Injection module for introducing controlled data errors into datasets.
Implements random value replacement, category misclassification, and MCAR missingness.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yaml

# Local imports
from random_seed import set_seed

logger = logging.getLogger(__name__)

##########################################################################
# Configuration loading
##########################################################################
def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a YAML configuration file. If ``config_path`` is None, the function
    looks for ``config/error_rates.yaml`` relative to the project root.
    """
    default_path = Path("config") / "error_rates.yaml"
    path = Path(config_path) if config_path else default_path
    if not path.is_file():
        logger.error("Configuration file not found: %s", path)
        raise FileNotFoundError(path)
    with open(path, "r") as f:
        cfg = yaml.safe_load(f)
    return cfg

##########################################################################
# Injection implementations
##########################################################################
def inject_random_replacement(
    df: pd.DataFrame,
    error_rate: float,
    seed: Optional[int] = None,
) -> Tuple[pd.DataFrame, int]:
    """
    Perform random value replacement on numeric columns.

    Parameters
    ----------
    df : pd.DataFrame
        The clean input dataframe.
    error_rate : float
        Proportion of rows to corrupt (e.g., 0.2 for 20 %).
    seed : int, optional
        Random seed for reproducibility. If ``None`` the global seed set by
        ``set_seed`` is used.

    Returns
    -------
    Tuple[pd.DataFrame, int]
        The corrupted dataframe and the number of rows that were modified.
    """
    if seed is not None:
        set_seed(seed)
    else:
        # Ensure deterministic behaviour if the caller has already set a seed
        set_seed(0)

    total_rows = len(df)
    n_replace = int(total_rows * error_rate)

    logger.debug(
        "Injecting random replacement: %d rows out of %d (rate=%.3f)",
        n_replace,
        total_rows,
        error_rate,
    )

    if n_replace == 0:
        return df.copy(), 0

    # Choose rows to replace without replacement
    replace_idx = np.random.choice(df.index, size=n_replace, replace=False)

    df_corrupted = df.copy()

    # Replace each numeric column with a uniform draw between its min and max
    numeric_cols = df_corrupted.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        col_min = df_corrupted[col].min()
        col_max = df_corrupted[col].max()
        # In the unlikely case min == max, keep the original value
        if col_min == col_max:
            random_vals = np.full(n_replace, col_min)
        else:
            random_vals = np.random.uniform(col_min, col_max, size=n_replace)
        df_corrupted.loc[replace_idx, col] = random_vals

    return df_corrupted, n_replace

def inject_category_misclassification(
    df: pd.DataFrame,
    error_rate: float,
    seed: Optional[int] = None,
) -> Tuple[pd.DataFrame, int]:
    """
    Placeholder for category misclassification injection.
    Currently raises NotImplementedError – to be completed in later tasks.
    """
    raise NotImplementedError(
        "Category misclassification injection not implemented yet."
    )

def inject_mcar_missingness(
    df: pd.DataFrame,
    error_rate: float,
    seed: Optional[int] = None,
) -> Tuple[pd.DataFrame, int]:
    """
    Placeholder for MCAR missingness injection.
    Currently raises NotImplementedError – to be completed in later tasks.
    """
    raise NotImplementedError("MCAR missingness injection not implemented yet.")

##########################################################################
# Orchestration helpers
##########################################################################
def run_injection(
    df: pd.DataFrame,
    error_type: str,
    error_rate: float,
    seed: Optional[int] = None,
) -> Tuple[pd.DataFrame, int]:
    """
    Dispatch to the appropriate injection routine based on ``error_type``.
    """
    if error_type == "replacement":
        return inject_random_replacement(df, error_rate, seed)
    elif error_type == "misclassification":
        return inject_category_misclassification(df, error_rate, seed)
    elif error_type == "mcar":
        return inject_mcar_missingness(df, error_rate, seed)
    else:
        raise ValueError(f"Unsupported error_type: {error_type}")

##########################################################################
# CLI entry point
##########################################################################
def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inject synthetic errors into a CSV dataset."
    )
    parser.add_argument(
        "input_csv", type=str, help="Path to the clean CSV file to corrupt."
    )
    parser.add_argument(
        "output_csv", type=str, help="Path where the corrupted CSV will be saved."
    )
    parser.add_argument(
        "--error-type",
        type=str,
        choices=["replacement", "misclassification", "mcar"],
        required=True,
        help="Type of error to inject.",
    )
    parser.add_argument(
        "--error-rate",
        type=float,
        required=True,
        help="Proportion of rows/cells to corrupt (0‑1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility.",
    )
    return parser.parse_args(argv)

def main(argv: Optional[List[str]] = None) -> None:
    args = _parse_args(argv)

    # Load data
    df = pd.read_csv(args.input_csv)

    # Perform injection
    corrupted_df, injected_cnt = run_injection(
        df,
        error_type=args.error_type,
        error_rate=args.error_rate,
        seed=args.seed,
    )

    # Save result
    os.makedirs(Path(args.output_csv).parent, exist_ok=True)
    corrupted_df.to_csv(args.output_csv, index=False)

    logger.info(
        "Injected %d rows (%s) into %s → %s",
        injected_cnt,
        args.error_type,
        args.input_csv,
        args.output_csv,
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
