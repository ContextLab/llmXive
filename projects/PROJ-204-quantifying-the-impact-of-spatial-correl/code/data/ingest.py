"""
data.ingest
=============

This module implements the high‑level ingestion workflow for the perovskite
solar‑cell dataset.  It orchestrates the steps that have already been
implemented elsewhere in the code‑base:

* ``download_data`` – fetches raw elemental map files.
* ``align_maps`` – resamples all maps onto a common pixel grid.
* ``mask_defects`` – masks dead pixels / artefacts in the aligned maps.

The new responsibility added for **T015** is to *validate* that every
sample contains the required performance metrics (PCE, J_sc, V_oc).  Any
sample missing one or more of these metrics is excluded from the final
dataset and a warning containing the offending ``sample_id`` is emitted.

The public API of this file (as declared in the project‑wide API surface)
consists of:

* ``ingest_and_filter_dataset`` – end‑to‑end entry point used by the
  pipeline.
* ``download_data`` – placeholder (already implemented elsewhere).
* ``align_maps`` – placeholder (already implemented elsewhere).
* ``mask_defects`` – placeholder (already implemented elsewhere).

The implementation below is self‑contained, uses only the declared public
names, and writes a concrete output file ``data/processed/validated_dataset.csv``.
"""

import logging
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
_LOGGER = logging.getLogger(__name__)
if not _LOGGER.handlers:
    # Configure a simple console logger if the user has not configured logging yet.
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)

# ----------------------------------------------------------------------
# Public functions (declared in the API surface)
# ----------------------------------------------------------------------
def ingest_and_filter_dataset(
    unified_dataset_path: Path = Path("data/processed/unified_dataset.csv"),
    output_path: Path = Path("data/processed/validated_dataset.csv"),
    performance_columns: Tuple[str, ...] = ("PCE", "J_sc", "V_oc"),
) -> pd.DataFrame:
    """
    End‑to‑end ingestion routine.

    1. Load the unified CSV produced by ``code/data/ingest.py`` (task T014c).
    2. Remove any rows where one of the required performance metrics is missing.
    3. Log a warning for each excluded ``sample_id``.
    4. Write the filtered dataframe to ``output_path``.
    5. Return the filtered dataframe for downstream consumers.

    Parameters
    ----------
    unified_dataset_path :
        Path to the CSV file containing the pre‑filter dataset.
    output_path :
        Destination path for the validated dataset.
    performance_columns :
        Column names that must be present and non‑null for a sample to be kept.

    Returns
    -------
    pd.DataFrame
        The filtered dataset.
    """
    _LOGGER.info("Starting ingestion and validation of dataset.")
    if not unified_dataset_path.is_file():
        raise FileNotFoundError(
            f"Unified dataset not found at {unified_dataset_path!s}. "
            "Make sure task T014c has been executed successfully."
        )

    df = pd.read_csv(unified_dataset_path)

    # Ensure the expected columns exist; otherwise raise a clear error.
    missing_cols = [col for col in performance_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"The unified dataset is missing required performance columns: {missing_cols}"
        )

    filtered_df, excluded_ids = _filter_missing_performance(df, performance_columns)

    # Log a warning for each excluded sample.
    for sample_id in excluded_ids:
        _LOGGER.warning(
            f"Excluding sample_id '{sample_id}' due to missing performance metrics."
        )

    # Write the validated dataset.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered_df.to_csv(output_path, index=False)
    _LOGGER.info(
        f"Validation complete. Kept {len(filtered_df)} samples; excluded {len(excluded_ids)}."
    )
    return filtered_df

def _filter_missing_performance(
    df: pd.DataFrame, performance_columns: Tuple[str, ...]
) -> Tuple[pd.DataFrame, List]:
    """
    Helper that drops rows with NaN in any of the required performance columns.

    Returns
    -------
    Tuple[pd.DataFrame, List]
        * The filtered dataframe.
        * List of ``sample_id`` values that were removed.
    """
    # Identify rows where any required performance metric is missing.
    mask_complete = df[performance_columns].notna().all(axis=1)
    filtered_df = df[mask_complete].copy()

    # Collect IDs of rows that were dropped.
    excluded_ids = df.loc[~mask_complete, "sample_id"].tolist()
    return filtered_df, excluded_ids

# ----------------------------------------------------------------------
# Place‑holder stubs for the functions that already exist elsewhere.
# They are re‑exported here to satisfy the declared public API.
# ----------------------------------------------------------------------
def download_data(*args, **kwargs):
    """
    Placeholder that forwards to the real implementation.

    The actual download logic lives in ``code/data/download.py`` (or a
    similar module).  Importing it lazily avoids circular imports.
    """
    from importlib import import_module

    module = import_module("data.download")
    return module.download_data(*args, **kwargs)

def align_maps(*args, **kwargs):
    """
    Forwarder to the real alignment implementation in ``code/data/align.py``.
    """
    from importlib import import_module

    module = import_module("data.align")
    return module.align_maps(*args, **kwargs)

def mask_defects(*args, **kwargs):
    """
    Forwarder to the defect‑masking implementation in ``code/preprocess/calibrate.py``.
    """
    from importlib import import_module

    module = import_module("preprocess.calibrate")
    return module.mask_defective_regions(*args, **kwargs)

# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    """
    Running this module directly will execute the ingestion + validation
    pipeline and produce ``validated_dataset.csv`` in the processed data
    directory.
    """
    ingest_and_filter_dataset()