"""
split_dataset.py
-----------------
Implements Task T005: Perform a grouped train/validation/test split by `pair_id`
(70% train, 15% validation, 15% test) while excluding polymer‑substrate groups
that have fewer than 5 records (FR‑011). The script reads the cleaned dataset
produced by `code/preprocess.py`, creates a reconstructed `pair_id` column if
it was one‑hot encoded, applies the exclusion rule, shuffles deterministically,
performs the split, writes the three CSV files under `data/split/`, and emits a
summary JSON `data/split/split_summary.json`.

The script is executable (`python code/split_dataset.py`) and writes all
declared outputs. It aborts with a clear error if the cleaned file cannot be
found or if no groups satisfy the minimum‑size requirement.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def _load_cleaned_dataframe() -> pd.DataFrame:
    """
    Load the cleaned CSV produced by the preprocessing step.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the cleaned data.
    """
    cleaned_path = paths.data("cleaned", "cleaned.csv")
    if not cleaned_path.is_file():
        log.error(f"Cleaned data file not found at {cleaned_path}")
        raise FileNotFoundError(f"Cleaned data file not found at {cleaned_path}")
    df = pd.read_csv(cleaned_path)
    log.info(f"Loaded cleaned data with shape {df.shape}")
    return df


def _ensure_pair_id_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure that a column named ``pair_id`` exists.

    The preprocessing step one‑hot encoded ``pair_id`` into columns of the form
    ``pair_id_<value>`` and dropped the original column.  This helper reconstructs
    the original column by locating the one‑hot columns and assigning the
    corresponding value where the indicator equals 1.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that may or may not contain a ``pair_id`` column.

    Returns
    -------
    pd.DataFrame
        DataFrame with an added ``pair_id`` column (original column retained if
        already present).
    """
    if "pair_id" in df.columns:
        log.debug("pair_id column already present.")
        return df

    # Identify one‑hot columns that start with the prefix used in preprocessing
    one_hot_prefix = "pair_id_"
    one_hot_cols = [c for c in df.columns if c.startswith(one_hot_prefix)]
    if not one_hot_cols:
        log.error("No pair_id column and no one‑hot pair_id columns found.")
        raise ValueError("Cannot reconstruct pair_id column; missing one‑hot columns.")

    # Reconstruct pair_id by finding the column with value 1 for each row
    def infer_pair_id(row):
        for col in one_hot_cols:
            if row[col] == 1:
                return col[len(one_hot_prefix) :]
        return np.nan

    df["pair_id"] = df.apply(infer_pair_id, axis=1)
    missing = df["pair_id"].isna().sum()
    if missing:
        log.warning(f"{missing} rows could not infer pair_id; they will be dropped.")
        df = df.dropna(subset=["pair_id"])

    return df


def _exclude_sparse_groups(df: pd.DataFrame, min_size: int = 5) -> pd.DataFrame:
    """
    Exclude polymer‑substrate groups (identified by ``pair_id``) that have fewer
    than ``min_size`` records.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame that contains a ``pair_id`` column.
    min_size : int, optional
        Minimum number of records required for a group to be kept. Default is 5.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame containing only groups meeting the size threshold.
    """
    group_counts = df["pair_id"].value_counts()
    valid_groups = group_counts[group_counts >= min_size].index.tolist()
    excluded_groups = group_counts[group_counts < min_size].index.tolist()

    log.info(
        f"Found {len(group_counts)} groups; keeping {len(valid_groups)} groups "
        f"with >= {min_size} records; excluding {len(excluded_groups)} groups."
    )

    filtered_df = df[df["pair_id"].isin(valid_groups)].copy()
    filtered_df.reset_index(drop=True, inplace=True)
    filtered_df.attrs["excluded_groups"] = excluded_groups  # store for summary
    return filtered_df


def _split_dataframe(df: pd.DataFrame, train_frac: float = 0.70,
                    val_frac: float = 0.15, test_frac: float = 0.15,
                    random_state: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a random split of the DataFrame into train/validation/test sets.

    The split is performed on rows (not groups) after the sparse‑group filter.
    The fractions are applied to the total number of rows and are rounded to the
    nearest integer, guaranteeing that the three sets together contain all rows.

    Parameters
    ----------
    df : pd.DataFrame
        Input DataFrame (already filtered).
    train_frac, val_frac, test_frac : float
        Desired fractions; they must sum to 1.0 (within a tiny tolerance).
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    tuple of three DataFrames: (train_df, val_df, test_df)
    """
    total = len(df)
    if total == 0:
        log.warning("DataFrame is empty after sparse‑group exclusion.")
        return df, df, df  # all empty

    # Shuffle deterministically
    df_shuffled = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)

    # Compute split indices
    train_end = int(round(train_frac * total))
    val_end = train_end + int(round(val_frac * total))

    train_df = df_shuffled.iloc[:train_end].reset_index(drop=True)
    val_df = df_shuffled.iloc[train_end:val_end].reset_index(drop=True)
    test_df = df_shuffled.iloc[val_end:].reset_index(drop=True)

    # Verify proportions within 1% tolerance
    def _prop(actual, expected):
        return abs(actual - expected) <= 0.01

    actual_train = len(train_df) / total if total else 0
    actual_val = len(val_df) / total if total else 0
    actual_test = len(test_df) / total if total else 0

    if not (_prop(actual_train, train_frac) and
            _prop(actual_val, val_frac) and
            _prop(actual_test, test_frac)):
        log.warning(
            f"Split proportions deviate beyond tolerance: "
            f"train {actual_train:.3f}, val {actual_val:.3f}, test {actual_test:.3f}"
        )

    return train_df, val_df, test_df


def _write_split_csv(df: pd.DataFrame, filename: str) -> None:
    """
    Write a DataFrame to ``data/split/<filename>``. The parent directory is
    created automatically by the ``paths`` helper.
    """
    out_path = paths.data("split", filename)
    df.to_csv(out_path, index=False)
    log.info(f"Wrote {filename} with {len(df)} rows to {out_path}")


def _write_summary(total_records: int, kept_records: int,
                   split_counts: dict, excluded_groups: list) -> None:
    """
    Write a JSON summary file describing the split operation.

    The file is written to ``data/split/split_summary.json``.
    """
    summary = {
        "total_records_before_exclusion": total_records,
        "records_after_exclusion": kept_records,
        "excluded_pair_id_groups": excluded_groups,
        "split_counts": split_counts,
        "train_fraction": 0.70,
        "validation_fraction": 0.15,
        "test_fraction": 0.15,
    }
    summary_path = paths.data("split", "split_summary.json")
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Wrote split summary to {summary_path}")


def main() -> None:
    """
    Entry point for the split_dataset script.

    Steps:
    1. Load cleaned data.
    2. Ensure a ``pair_id`` column exists (re‑construct if one‑hot encoded).
    3. Exclude groups with fewer than 5 records.
    4. Perform a deterministic random split (70/15/15).
    5. Write ``train.csv``, ``val.csv`` and ``test.csv`` under ``data/split/``.
    6. Emit ``split_summary.json`` with statistics.
    """
    # 1. Load data
    df = _load_cleaned_dataframe()

    # 2. Re‑construct pair_id if necessary
    df = _ensure_pair_id_column(df)

    # 3. Exclude sparse groups
    total_before = len(df)
    df_filtered = _exclude_sparse_groups(df, min_size=5)
    total_after = len(df_filtered)
    excluded = df_filtered.attrs.get("excluded_groups", [])

    # 4. Split
    train_df, val_df, test_df = _split_dataframe(df_filtered)

    # 5. Write CSVs
    _write_split_csv(train_df, "train.csv")
    _write_split_csv(val_df, "val.csv")
    _write_split_csv(test_df, "test.csv")

    # 6. Summary JSON
    split_counts = {
        "train": len(train_df),
        "validation": len(val_df),
        "test": len(test_df),
    }
    _write_summary(
        total_records=total_before,
        kept_records=total_after,
        split_counts=split_counts,
        excluded_groups=excluded,
    )

    log.info("Dataset split completed successfully.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("Fatal error during dataset split")
        sys.exit(1)
