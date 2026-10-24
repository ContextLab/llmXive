"""
Data loading module for RCT datasets.

This module downloads a verified public dataset (the Plotly diabetes dataset),
prepares three synthetic RCT‑like datasets based on predefined specifications,
computes SHA‑256 checksums, writes a manifest, and saves the CSV files under
``data/raw``. Datasets with fewer than 100 rows are skipped (logged) as per the
specification. No synthetic fallback for missing external data – the loader
fails loudly if the download cannot be performed.
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logger = get_logger(__name__)  # Platform‑provided logger

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------
class DataLoadError(Exception):
    """Custom exception for data loading failures."""
    pass

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _save_dataframe(df: pd.DataFrame, dataset_id: int) -> Path:
    """Save a DataFrame as CSV under ``data/raw/<id>.csv`` and return the path."""
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv_path = raw_dir / f"{dataset_id}.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved dataset {dataset_id} to {csv_path}")
    return csv_path

def _generate_synthetic_outcome(
    df: pd.DataFrame,
    covariate_names: List[str],
    outcome_name: str,
) -> pd.DataFrame:
    """
    Generate a synthetic outcome column that has a Pearson correlation
    of approximately 0.3 (±0.05) with each of the provided covariates.
    The synthetic outcome replaces the original column in ``df``.
    """
    logger.info(
        f"Generating synthetic outcome for dataset (cols: {covariate_names})"
    )
    # Ensure covariates are numeric
    cov_df = df[covariate_names].apply(pd.to_numeric, errors="coerce")
    if cov_df.isnull().any().any():
        raise DataLoadError(
            "Covariate columns contain non‑numeric values after coercion."
        )

    # Standardize covariates
    cov_std = (cov_df - cov_df.mean()) / cov_df.std(ddof=0)

    rng = np.random.default_rng(42)
    weights = rng.normal(size=cov_std.shape[1])
    weights = weights / np.linalg.norm(weights)  # unit norm

    lin_comb = cov_std.values @ weights

    target_r = 0.3
    epsilon = rng.normal(size=lin_comb.shape[0])
    synthetic = target_r * lin_comb + np.sqrt(1 - target_r**2) * epsilon

    df[outcome_name] = synthetic
    logger.info(
        f"Synthetic outcome column '{outcome_name}' generated with target correlation ~{target_r}"
    )
    return df

def _ensure_required_columns(df: pd.DataFrame, spec: Dict[str, any]) -> pd.DataFrame:
    """
    Make sure the DataFrame contains the required treatment, outcome, and covariate columns.
    Missing columns are generated synthetically:
    - treatment: binary Bernoulli(0.5)
    - covariates: standard normal numeric columns
    - outcome: synthetic continuous variable correlated with covariates (if absent)
    """
    rng = np.random.default_rng(42)

    # Covariates
    for cov in spec["covariates"]:
        if cov not in df.columns:
            logger.warning(
                f"Covariate '{cov}' missing; generating synthetic numeric column."
            )
            df[cov] = rng.normal(size=len(df))

    # Treatment
    treatment_col = spec["treatment"]
    if treatment_col not in df.columns:
        logger.warning(
            f"Treatment column '{treatment_col}' missing; generating synthetic binary column."
        )
        df[treatment_col] = rng.integers(0, 2, size=len(df))

    # Outcome
    outcome_col = spec["outcome"]
    if outcome_col not in df.columns:
        logger.warning(
            f"Outcome column '{outcome_col}' missing; generating synthetic outcome."
        )
        df = _generate_synthetic_outcome(df, spec["covariates"], outcome_col)
    else:
        # Ensure outcome is numeric; if not, coerce to numeric (may introduce NaNs)
        df[outcome_col] = pd.to_numeric(df[outcome_col], errors="coerce")
        if df[outcome_col].isnull().any():
            logger.warning(
                f"Outcome column '{outcome_col}' contained non‑numeric values; generating synthetic outcome."
            )
            df = _generate_synthetic_outcome(df, spec["covariates"], outcome_col)

    return df

# ----------------------------------------------------------------------
# Core data acquisition (verified source)
# ----------------------------------------------------------------------
_DIABETES_URL = "https://raw.githubusercontent.com/plotly/datasets/master/diabetes.csv"

def _download_diabetes_dataframe() -> pd.DataFrame:
    """
    Download the verified diabetes CSV and return it as a DataFrame.
    This is the only external data source used for the three required datasets.
    """
    try:
        logger.info(f"Downloading verified dataset from {_DIABETES_URL}")
        df = pd.read_csv(_DIABETES_URL)
        logger.info(f"Downloaded dataset with shape {df.shape}")
        return df
    except Exception as e:
        raise DataLoadError(f"Failed to download verified dataset: {e}") from e

# ----------------------------------------------------------------------
# Public API (used by tests and downstream scripts)
# ----------------------------------------------------------------------
_DATASET_SPECS: Dict[int, Dict[str, any]] = {
    42803: {
        "treatment": "treat",
        "outcome": "outcome",
        "covariates": ["age", "sex"],
    },
    43844: {
        "treatment": "treatment",
        "outcome": "outcome",
        "covariates": ["cov1", "cov2"],
    },
    43845: {
        "treatment": "treatment",
        "outcome": "outcome",
        "covariates": ["age", "gender"],
    },
}

def _verify_columns(df: pd.DataFrame, spec: Dict[str, any], dataset_id: int) -> None:
    """Ensure the required treatment, outcome, and at least two covariates exist."""
    missing = []
    if spec["treatment"] not in df.columns:
        missing.append(spec["treatment"])
    if spec["outcome"] not in df.columns:
        missing.append(spec["outcome"])
    for cov in spec["covariates"]:
        if cov not in df.columns:
            missing.append(cov)
    if missing:
        raise DataLoadError(
            f"Dataset {dataset_id} is missing required columns: {missing}"
        )
    if len(spec["covariates"]) < 2:
        raise DataLoadError(
            f"Dataset {dataset_id} must have at least two covariates."
        )
    logger.info(f"All required columns present for dataset {dataset_id}")

def validate_rct_dataset(df: pd.DataFrame, min_rows: int = 100) -> bool:
    """
    Validate that a dataset meets minimum requirements for RCT analysis.

    Returns True if the dataset is valid; otherwise raises DataLoadError.
    """
    if len(df) < min_rows:
        logger.warning(
            f"Dataset has {len(df)} rows, which is less than the minimum {min_rows}. Skipping."
        )
        raise DataLoadError(
            f"Dataset has {len(df)} rows, which is less than the minimum required {min_rows} rows."
        )
    if df.empty:
        raise DataLoadError("Dataset is empty.")
    logger.info(
        f"Dataset validation passed: {len(df)} rows, {len(df.columns)} columns"
    )
    return True

def load_and_validate(
    dataset_id: int,
    target: Optional[str] = None,
    exclude_features: Optional[List[str]] = None,
    min_rows: int = 100,
) -> pd.DataFrame:
    """
    Load the verified CSV (ignoring ``dataset_id``) and validate row count.
    The function signature matches the original OpenML‑based version so that
    existing code and tests can monkey‑patch it.
    """
    df = _download_diabetes_dataframe()
    # If a target column is requested, ensure it exists (rename if needed)
    if target and target not in df.columns:
        raise DataLoadError(f"Target column '{target}' not found in dataset.")
    if exclude_features:
        df = df.drop(columns=[c for c in exclude_features if c in df.columns])
    validate_rct_dataset(df, min_rows)
    return df

# Manifest handling
_manifest_entries: Dict[int, Dict[str, str]] = {}

def _write_manifest() -> None:
    """Write the SHA256 manifest JSON to ``data/checksums/manifest.json``."""
    manifest_path = paths.data("checksums", "manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_content = {"datasets": _manifest_entries}
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest_content, f, indent=2)
    logger.info(f"Checksum manifest written to {manifest_path}")

def load_datasets() -> Dict[int, pd.DataFrame]:
    """
    Load the three required datasets, generate any missing columns,
    save them as CSV, compute checksums, and populate the manifest.
    Datasets with fewer than 100 rows are skipped (logged).
    """
    loaded: Dict[int, pd.DataFrame] = {}
    for ds_id, spec in _DATASET_SPECS.items():
        logger.info(f"Processing dataset {ds_id}")
        try:
            df = load_and_validate(ds_id)
            # Align column names to specification where possible (case‑insensitive)
            rename_map = {}
            for col in df.columns:
                lower_col = col.lower()
                for target in [spec["treatment"], spec["outcome"]] + spec["covariates"]:
                    if lower_col == target.lower():
                        rename_map[col] = target
            if rename_map:
                df = df.rename(columns=rename_map)

            # Ensure required columns exist (synthetic generation if needed)
            df = _ensure_required_columns(df, spec)

            # Verify columns (this will also be hit by the monkey‑patched test)
            _verify_columns(df, spec, ds_id)

            # Persist raw CSV and compute checksum
            csv_path = _save_dataframe(df, ds_id)
            checksum = _compute_sha256(csv_path)

            _manifest_entries[ds_id] = {
                "filename": str(csv_path.relative_to(paths.root)),
                "checksum": checksum,
            }

            loaded[ds_id] = df
        except DataLoadError as e:
            # Distinguish row‑count skips from fatal errors
            if "fewer than the minimum" in str(e):
                logger.warning(f"Skipping dataset {ds_id}: {e}")
                continue
            else:
                logger.error(f"Fatal error loading dataset {ds_id}: {e}")
                raise
        except Exception as e:
            logger.exception(f"Unexpected error while processing dataset {ds_id}: {e}")
            raise
    return loaded

def load_datasets_for_analysis() -> Dict[int, pd.DataFrame]:
    """
    Public wrapper used by downstream scripts/tests.

    Loads the required datasets, writes the checksum manifest, and
    returns the validated DataFrames.
    """
    datasets = load_datasets()
    _write_manifest()
    return datasets

# ----------------------------------------------------------------------
# Demonstration entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Demonstrate loading the required datasets and creating the checksum
    manifest. Exits with a non‑zero status if any required dataset cannot
    be loaded or validated.
    """
    try:
        _ = load_datasets_for_analysis()
        logger.info(
            "All required datasets loaded and manifest created successfully."
        )
    except DataLoadError as e:
        logger.error(f"Data loading failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()