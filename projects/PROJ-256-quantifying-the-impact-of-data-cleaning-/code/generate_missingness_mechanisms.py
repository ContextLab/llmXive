"""
Missingness mechanism generation utilities.

This script creates two missing‑data masks for each raw dataset:

* **MCAR** – Missing Completely At Random.  A uniform random mask is
  generated with a configurable missing‑rate.
* **MAR** – Missing At Random.  A logistic‑regression‑based mask is
  generated where the probability of a missing value depends on the
  other features (simulating a realistic MAR mechanism).

The resulting masks are saved as ``.npz`` files in
``data/processed/missingness_mechanisms/`` with the same stem as the
original dataset file.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.utils import shuffle
from sklearn.preprocessing import StandardScaler

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def generate_mcar_mask(
    df: pd.DataFrame,
    missing_rate: float = 0.1,
    random_state: Optional[int] = None,
) -> np.ndarray:
    """
    Generate a MCAR (Missing Completely At Random) mask.

    Parameters
    ----------
    df : pd.DataFrame
        Input data frame (shape is used for mask dimensions).
    missing_rate : float, optional
        Proportion of entries to set as missing.  Must be between 0 and 1.
        Defaults to ``0.1`` (10 % missing).
    random_state : int, optional
        Seed for reproducibility.

    Returns
    -------
    np.ndarray
        Boolean array of shape ``df.shape`` where ``True`` indicates a
        missing entry.
    """
    rng = np.random.default_rng(random_state)
    mask = rng.random(df.shape) < missing_rate
    return mask

def generate_mar_mask(
    df: pd.DataFrame,
    target_column: Optional[str] = None,
    missing_rate: float = 0.1,
    random_state: Optional[int] = None,
) -> np.ndarray:
    """
    Generate a MAR (Missing At Random) mask using a logistic model.

    The mask is generated only for the *target* column (or the first
    column if ``target_column`` is ``None``).  The probability of a missing
    entry is made a function of the remaining features.

    Parameters
    ----------
    df : pd.DataFrame
        Input data.
    target_column : str, optional
        Column to which the MAR mask will be applied.  If omitted the
        first column is used.
    missing_rate : float, optional
        Desired overall missing proportion in the target column.
    random_state : int, optional
        Seed for reproducibility.

    Returns
    -------
    np.ndarray
        Boolean mask with the same shape as ``df`` where only the target
        column may contain ``True`` values.
    """
    rng = np.random.default_rng(random_state)

    if target_column is None:
        target_column = df.columns[0]

    # Features are all columns except the target
    X = df.drop(columns=[target_column]).values
    y = df[target_column].values

    # Standardise features for logistic regression stability
    scaler = StandardScaler()
    X_std = scaler.fit_transform(X)

    # Create a synthetic binary indicator that will be used as the
    # "missingness" label.  Its probability is correlated with the target.
    # This mimics MAR where missingness depends on observed data.
    prob_missing = 1 / (1 + np.exp(-0.5 * (y - np.mean(y))))
    synthetic_missing = rng.binomial(1, prob_missing)

    # Fit logistic regression to predict the synthetic missingness from X
    model = LogisticRegression(solver="lbfgs", max_iter=200)
    model.fit(X_std, synthetic_missing)

    # Predict probabilities of missingness for each row
    pred_prob = model.predict_proba(X_std)[:, 1]

    # Choose a threshold that yields approximately the requested missing_rate
    threshold = np.quantile(pred_prob, 1 - missing_rate)
    missing_indicator = pred_prob >= threshold

    # Build full mask (only target column gets missing values)
    mask = np.zeros(df.shape, dtype=bool)
    target_idx = df.columns.get_loc(target_column)
    mask[:, target_idx] = missing_indicator
    return mask

def apply_missingness_to_df(df: pd.DataFrame, mask: np.ndarray) -> pd.DataFrame:
    """
    Apply a missingness mask to a DataFrame, setting masked entries to ``NaN``.

    Parameters
    ----------
    df : pd.DataFrame
        Original data.
    mask : np.ndarray
        Boolean mask of the same shape as ``df``.  ``True`` entries become
        ``NaN`` in the returned copy.

    Returns
    -------
    pd.DataFrame
        New DataFrame with missing values introduced.
    """
    df_copy = df.copy()
    df_copy.where(~mask, other=np.nan, inplace=True)
    return df_copy

# ----------------------------------------------------------------------
# Core processing routine
# ----------------------------------------------------------------------
def process_dataset(
    raw_path: Path,
    output_dir: Path,
    missing_rate: float = 0.1,
    random_state: Optional[int] = None,
) -> None:
    """
    Process a single dataset: generate MCAR and MAR masks and store them.

    The function writes a ``.npz`` file containing two arrays:
    ``mcar`` and ``mar``.  The file name mirrors the source dataset name.

    Parameters
    ----------
    raw_path : pathlib.Path
        Path to the raw CSV file.
    output_dir : pathlib.Path
        Directory where the ``.npz`` mask file will be saved.
    missing_rate : float, optional
        Desired proportion of missing entries (default ``0.1``).
    random_state : int, optional
        Seed for reproducibility.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing dataset {raw_path.name}")

    df = pd.read_csv(raw_path)

    # Determine a sensible target column for MAR – use a column named
    # ``target`` / ``outcome`` if present, otherwise the first column.
    possible_targets = [c for c in df.columns if c.lower() in {"target", "outcome", "y"}]
    target_col = possible_targets[0] if possible_targets else df.columns[0]

    mcar_mask = generate_mcar_mask(df, missing_rate, random_state)
    mar_mask = generate_mar_mask(df, target_column=target_col, missing_rate=missing_rate, random_state=random_state)

    # Save masks; we keep the original DataFrame untouched – downstream
    # scripts will apply the masks as needed.
    output_path = output_dir / f"{raw_path.stem}_missingness.npz"
    np.savez_compressed(output_path, mcar=mcar_mask, mar=mar_mask)

    logger.info(f"Saved missingness mechanisms to {output_path}")

# ----------------------------------------------------------------------
# Command‑line interface
# ----------------------------------------------------------------------
def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate MCAR and MAR missingness mechanisms for each raw dataset."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data/raw"),
        help="Directory containing raw CSV datasets (default: data/raw).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed/missingness_mechanisms"),
        help="Directory where mask files will be written (default: data/processed/missingness_mechanisms).",
    )
    parser.add_argument(
        "--missing-rate",
        type=float,
        default=0.1,
        help="Proportion of entries to mask as missing (default: 0.1).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    return parser.parse_args()

def main() -> None:
    """
    Entry point for the ``generate_missingness_mechanisms`` script.

    The function respects the same environment variables used elsewhere in
    the project (e.g. ``DATASET_URLS``) but defaults to the conventional
    directory layout if they are absent.
    """
    args = _parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialise simple console logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Iterate over CSV files in the raw directory
    csv_files = list(args.raw_dir.glob("*.csv"))
    if not csv_files:
        logging.error(f"No CSV files found in {args.raw_dir}")
        raise FileNotFoundError(f"No CSV files found in {args.raw_dir}")

    for csv_path in csv_files:
        process_dataset(
            raw_path=csv_path,
            output_dir=args.output_dir,
            missing_rate=args.missing_rate,
            random_state=args.seed,
        )

if __name__ == "__main__":
    main()
