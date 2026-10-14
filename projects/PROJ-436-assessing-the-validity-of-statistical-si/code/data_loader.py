"""
Data loading module for RCT datasets from OpenML.

This module handles downloading, caching, validating, and recording
checksums for the required public RCT datasets. It enforces strict
failure‑on‑error semantics: any fetch or conversion error for a required
dataset raises an exception and aborts the loading process. Datasets with
fewer than 100 rows are skipped (logged) as per the specification.
If a dataset’s outcome column is fully observed, a synthetic outcome is
generated that preserves a Pearson correlation of approximately 0.3 (±0.05)
with the covariates, and this action is logged.
"""

import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import openml
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
        f"Generating synthetic outcome for MNAR edge‑case (dataset columns: {covariate_names})"
    )
    # Ensure covariates are numeric; coerce if needed
    cov_df = df[covariate_names].apply(pd.to_numeric, errors="coerce")
    # Drop rows with NaNs in covariates – they will be handled later by missingness simulation
    cov_df = cov_df.dropna()
    if cov_df.empty:
        raise DataLoadError(
            "Cannot generate synthetic outcome: covariate columns are empty after dropping NaNs."
        )

    # Standardize covariates
    cov_std = (cov_df - cov_df.mean()) / cov_df.std(ddof=0)

    # Random weights for a linear combination
    rng = np.random.default_rng(42)
    weights = rng.normal(size=cov_std.shape[1])
    weights = weights / np.linalg.norm(weights)  # unit norm

    # Linear combination
    lin_comb = cov_std.values @ weights

    # Scale to achieve target correlation r ≈ 0.3
    target_r = 0.3
    epsilon = rng.normal(size=lin_comb.shape[0])
    synthetic = target_r * lin_comb + np.sqrt(1 - target_r**2) * epsilon

    # Align synthetic outcome with original index
    outcome_series = pd.Series(data=np.nan, index=df.index, name=outcome_name)
    outcome_series.loc[cov_df.index] = synthetic

    df[outcome_name] = outcome_series
    logger.info(
        f"Synthetic outcome column '{outcome_name}' generated with target correlation ~{target_r}"
    )
    return df

# ----------------------------------------------------------------------
# Core OpenML interaction
# ----------------------------------------------------------------------
def get_openml_dataset(dataset_id: int) -> openml.datasets.OpenMLDataset:
    """
    Download or retrieve a dataset from OpenML by ID.

    Raises:
        DataLoadError: If the dataset cannot be found or downloaded.
    """
    try:
        logger.info(f"Fetching dataset {dataset_id} from OpenML...")
        # ``download_data=False`` forces OpenML to keep the raw files cached;
        # ``get_data`` will handle conversion using pandas (requires pyarrow for parquet).
        dataset = openml.datasets.get_dataset(dataset_id, download_data=False)
        logger.info(
            f"Successfully retrieved dataset: {dataset.name} (ID: {dataset_id})"
        )
        return dataset
    except openml.exceptions.OpenMLServerException as e:
        if "not found" in str(e).lower():
            raise DataLoadError(
                f"Dataset with ID {dataset_id} not found on OpenML."
            ) from e
        raise DataLoadError(
            f"OpenML server error while fetching dataset {dataset_id}: {e}"
        ) from e
    except Exception as e:
        raise DataLoadError(
            f"Failed to download dataset {dataset_id}: {e}"
        ) from e

def load_dataset_as_dataframe(
    dataset: openml.datasets.OpenMLDataset,
    target: Optional[str] = None,
    exclude_features: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Convert an OpenML dataset to a pandas DataFrame.

    Raises:
        DataLoadError: If the dataset cannot be converted to a DataFrame.
    """
    try:
        X, y, _, _ = dataset.get_data(
            target=target, dataset_format="dataframe"
        )
        if target and y is not None:
            if target not in X.columns:
                X[target] = y
        if exclude_features:
            X = X.drop(
                columns=[f for f in exclude_features if f in X.columns]
            )
        logger.info(f"Loaded dataset with shape: {X.shape}")
        return X
    except Exception as e:
        raise DataLoadError(
            f"Failed to convert dataset to DataFrame: {e}"
        ) from e

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
    Load and validate a dataset from OpenML.

    Raises DataLoadError on any failure.
    """
    dataset = get_openml_dataset(dataset_id)
    df = load_dataset_as_dataframe(dataset, target, exclude_features)
    validate_rct_dataset(df, min_rows)
    return df

# ----------------------------------------------------------------------
# Specification‑driven loader for the three required datasets
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

def load_datasets() -> Dict[int, pd.DataFrame]:
    """
    Load the three RCT datasets required for the study.

    Returns a dictionary mapping OpenML dataset IDs to validated pandas
    DataFrames. Datasets with fewer than 100 rows are skipped (logged).
    Any other error aborts the loading process.
    """
    loaded: Dict[int, pd.DataFrame] = {}
    for ds_id, spec in _DATASET_SPECS.items():
        logger.info(f"Processing dataset {ds_id}")
        try:
            df = load_and_validate(ds_id)
            _verify_columns(df, spec, ds_id)

            # MNAR edge‑case handling
            outcome_col = spec["outcome"]
            if df[outcome_col].isnull().sum() == 0:
                logger.warning(
                    f"Outcome column '{outcome_col}' in dataset {ds_id} is fully observed. "
                    "Generating synthetic outcome for MNAR simulation."
                )
                df = _generate_synthetic_outcome(
                    df, spec["covariates"], outcome_col
                )

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
                # Re‑raise to fail loudly as required
                raise
        except Exception as e:
            logger.exception(
                f"Unexpected error while processing dataset {ds_id}: {e}"
            )
            raise
    return loaded

# ----------------------------------------------------------------------
# Manifest handling
# ----------------------------------------------------------------------
_manifest_entries: Dict[int, Dict[str, str]] = {}

def _write_manifest() -> None:
    """Write the SHA256 manifest JSON to ``data/checksums/manifest.json``."""
    manifest_path = paths.data("checksums", "manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_content = {"datasets": _manifest_entries}
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest_content, f, indent=2)
    logger.info(f"Checksum manifest written to {manifest_path}")

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
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
