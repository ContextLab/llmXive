"""
Preprocessing steps for target-variable validation and row exclusion.

T011: check that the target variable (conductivity) spans at least three
orders of magnitude (log10 range >= 3). If the check fails, the script
aborts with a non-zero exit code; otherwise it writes a JSON file with
the minimum, maximum, and log10 range of the target.

T012: exclude molecules with missing conductivity or invalid descriptors
from the training set, logging counts to
``data/processed/exclusion_log.json`` and writing the retained rows to
``data/processed/filtered_train.csv``.
"""

import json
import logging
import sys

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DEFAULT_TARGET_COLUMN = "conductivity"
MIN_LOG10_RANGE = 3.0  # required dynamic range


def _load_input_dataframe() -> pd.DataFrame:
    """
    Load the raw input CSV that contains at least a ``smiles`` column and the
    target variable (by default ``conductivity``). The data loader may have
    produced either ``input.csv`` or ``smiles.csv`` in ``data/raw``.
    """
    raw_dir = paths.data("raw")
    input_path = raw_dir / "input.csv"
    if not input_path.exists():
        input_path = raw_dir / "smiles.csv"
    if not input_path.exists():
        log.error(f"Neither 'input.csv' nor 'smiles.csv' found in {raw_dir}.")
        raise FileNotFoundError("Raw input CSV not found.")
    try:
        df = pd.read_csv(input_path)
    except Exception as exc:
        log.error(f"Failed to read raw input CSV '{input_path}': {exc}")
        raise
    return df


def compute_dynamic_range(df: pd.DataFrame, target_col: str = DEFAULT_TARGET_COLUMN) -> dict:
    """
    Compute the dynamic range of ``target_col`` in log10 units.

    Returns a dict with keys ``min``, ``max``, and ``range_log10``.
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    # Drop missing values
    values = df[target_col].dropna()
    if values.empty:
        raise ValueError(f"No non-missing values found for target column '{target_col}'.")

    # Conductivity must be strictly positive to compute a logarithm
    if (values <= 0).any():
        raise ValueError("Target column contains non-positive values; cannot compute log10 range.")

    min_val = float(values.min())
    max_val = float(values.max())
    range_log10 = float(np.log10(max_val) - np.log10(min_val))

    return {"min": min_val, "max": max_val, "range_log10": range_log10}


# ---------------------------------------------------------------------------
# T012: exclusion of molecules with missing conductivity / invalid descriptors
# ---------------------------------------------------------------------------

def _numeric_descriptor_columns(df: pd.DataFrame, target_col: str) -> list:
    """Return the numeric descriptor columns of ``df`` (excluding ids/target)."""
    skip = {"smiles", "smiles_id", "name", target_col,
            f"log_{target_col}", "scaffold_id"}
    return [
        c for c in df.columns
        if c not in skip and pd.api.types.is_numeric_dtype(df[c])
    ]


def exclude_invalid_rows(
    df: pd.DataFrame,
    target_col: str = DEFAULT_TARGET_COLUMN,
    descriptor_cols=None,
):
    """
    Exclude molecules with missing conductivity or invalid descriptors.

    A row is excluded when:
    * its target value is missing, non-numeric, or non-positive
      (conductivity must be positive to be log-transformed), or
    * any of its numeric descriptor values is NaN or non-finite.

    Returns
    -------
    (clean_df, exclusion_log) : tuple
        ``clean_df`` contains only the valid rows; ``exclusion_log`` is a
        dict with counts ``missing_conductivity`` and
        ``invalid_descriptors`` (plus totals).
    """
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in DataFrame.")

    df = df.copy()
    total = len(df)

    # --- missing / invalid target -------------------------------------
    vals = pd.to_numeric(df[target_col], errors="coerce")
    missing_target = vals.isna() | (vals <= 0)
    # Rows excluded solely because of the target (not already counted
    # below for descriptor problems).
    missing_conductivity_count = int(missing_target.sum())

    # --- invalid descriptors ------------------------------------------
    if descriptor_cols is None:
        descriptor_cols = _numeric_descriptor_columns(df, target_col)
    descriptor_cols = [c for c in descriptor_cols if c in df.columns]

    invalid_desc = pd.Series(False, index=df.index)
    for col in descriptor_cols:
        num = pd.to_numeric(df[col], errors="coerce")
        invalid_desc |= num.isna() | ~np.isfinite(num.astype(float))
    invalid_descriptors_count = int((invalid_desc & ~missing_target).sum())

    keep_mask = ~missing_target & ~invalid_desc
    clean_df = df.loc[keep_mask].reset_index(drop=True)

    exclusion_log = {
        "total_input": total,
        "missing_conductivity": missing_conductivity_count,
        "invalid_descriptors": invalid_descriptors_count,
        "total_excluded": int((~keep_mask).sum()),
        "retained": int(keep_mask.sum()),
        "target_column": target_col,
        "descriptor_columns_checked": descriptor_cols,
    }
    return clean_df, exclusion_log


def _load_exclusion_input() -> pd.DataFrame:
    """
    Load the data used for the exclusion step.

    Prefers ``data/processed/descriptors.csv`` (merging the conductivity
    column from the raw input on the ``smiles`` key when needed); falls
    back to the raw input CSV itself.
    """
    desc_path = paths.data("processed", "descriptors.csv")
    raw_df = _load_input_dataframe()

    if desc_path.exists():
        desc_df = pd.read_csv(desc_path)
        if DEFAULT_TARGET_COLUMN in desc_df.columns:
            return desc_df
        if "smiles" in desc_df.columns and "smiles" in raw_df.columns:
            targets = raw_df[["smiles", DEFAULT_TARGET_COLUMN]].drop_duplicates("smiles")
            merged = desc_df.merge(targets, on="smiles", how="left")
            return merged
        return desc_df
    return raw_df


def run_exclusion(target_col: str = DEFAULT_TARGET_COLUMN) -> int:
    """
    T012 entry point: exclude invalid molecules, write
    ``data/processed/exclusion_log.json`` and
    ``data/processed/filtered_train.csv``.
    """
    try:
        df = _load_exclusion_input()
    except Exception as exc:
        log.error(f"Unable to load data for exclusion: {exc}")
        return 1

    try:
        clean_df, exclusion_log = exclude_invalid_rows(df, target_col)
    except Exception as exc:
        log.error(f"Exclusion step failed: {exc}")
        return 1

    if exclusion_log["missing_conductivity"] > 0:
        log.warning(
            f"Excluded {exclusion_log['missing_conductivity']} molecules "
            f"with missing/invalid {target_col}."
        )
    if exclusion_log["invalid_descriptors"] > 0:
        log.warning(
            f"Excluded {exclusion_log['invalid_descriptors']} molecules "
            f"with invalid descriptors."
        )

    processed = paths.data("processed")
    log_path = processed / "exclusion_log.json"
    with open(log_path, "w") as f:
        json.dump(exclusion_log, f, indent=2)
    log.info(f"Exclusion log written to {log_path}")

    train_path = processed / "filtered_train.csv"
    clean_df.to_csv(train_path, index=False)
    log.info(
        f"Filtered training set ({len(clean_df)} rows) written to {train_path}"
    )
    return 0


def main() -> int:
    """
    Entry point used by the pipeline.

    - Loads the raw input CSV.
    - Computes the dynamic range of the conductivity column (T011).
    - Aborts with exit code 1 if the range is < 3 log10 units.
    - Writes ``data/processed/target_dynamic_range.json`` otherwise.
    - Runs the T012 exclusion step, writing ``exclusion_log.json`` and
      ``filtered_train.csv``.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # --- T011: dynamic range validation --------------------------------
    try:
        df = _load_input_dataframe()
    except Exception:
        log.exception("Unable to load input data.")
        return 1

    try:
        stats = compute_dynamic_range(df, DEFAULT_TARGET_COLUMN)
    except Exception as exc:
        log.error(f"Dynamic-range calculation failed: {exc}")
        return 1

    if stats["range_log10"] < MIN_LOG10_RANGE:
        log.error(
            f"Target dynamic range insufficient: {stats['range_log10']:.2f} log10 units "
            f"(minimum required: {MIN_LOG10_RANGE})."
        )
        return 1

    out_path = paths.data("processed", "target_dynamic_range.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(out_path, "w") as f:
            json.dump(stats, f, indent=2)
    except Exception as exc:
        log.error(f"Failed to write JSON output: {exc}")
        return 1

    log.info(f"Target dynamic range validated and written to {out_path}")

    # --- T012: exclusion of invalid molecules ---------------------------
    return run_exclusion()


if __name__ == "__main__":
    raise SystemExit(main())
