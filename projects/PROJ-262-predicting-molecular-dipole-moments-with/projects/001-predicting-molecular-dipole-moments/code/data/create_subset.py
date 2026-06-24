"""
create_subset.py
-----------------
Create a reproducible random 10,000‑molecule subset of the QM9 dataset.

The script is part of the *User Story 1* data‑preparation pipeline.  It
assumes that the raw QM9 data have either already been downloaded by
``download_qm9.py`` and stored as ``data/raw/qm9.parquet`` or that the
HuggingFace ``datasets`` library can fetch the dataset on‑the‑fly.

The resulting subset is written to ``data/processed/molecules_10k.parquet``.
The file can be consumed by downstream preprocessing steps (3‑D coordinate
extraction, 2‑D descriptor generation, …).

The implementation provides:
  * a ``create_subset`` function that can be imported in tests or other
    modules,
  * a command‑line interface for ad‑hoc execution,
  * deterministic sampling via a configurable random seed,
  * graceful handling of missing raw files.

Dependencies
------------
* ``datasets`` – for loading the QM9 dataset from HuggingFace.
* ``pandas`` – for DataFrame manipulation and Parquet export.
* ``pyarrow`` – Parquet engine (installed as a pandas optional dependency).

Both ``datasets`` and ``pandas`` are expected to be listed in
``requirements.txt`` already; if they are not, the project’s ``requirements.txt``
should be updated accordingly.
"""

import argparse
import logging
import os
from pathlib import Path
from typing import Optional

try:
    # ``set_seed`` is part of the reproducibility utilities defined elsewhere
    # in the project (e.g., ``code/utils/reproducibility.py``).  If it is not
    # available we fall back to setting the NumPy and Python random seeds
    # directly.
    from code.utils.reproducibility import set_seed  # type: ignore
except Exception:  # pragma: no cover
    set_seed = None  # type: ignore

import numpy as np
import pandas as pd

# ``datasets`` is a heavy optional dependency; we import it lazily inside the
# function that needs it so that the module can be imported even in minimal
# environments (e.g., during static analysis).
from datasets import load_dataset  # type: ignore

logger = logging.getLogger(__name__)

DEFAULT_RAW_PARQUET = Path("data/raw/qm9.parquet")
DEFAULT_OUTPUT_PARQUET = Path("data/processed/molecules_10k.parquet")
DEFAULT_SAMPLE_SIZE = 10_000
DEFAULT_SEED = 42


def _load_raw_qm9() -> pd.DataFrame:
    """
    Load the full QM9 dataset.

    The function first looks for a locally cached Parquet file at
    ``data/raw/qm9.parquet``.  If the file does not exist, it falls back to
    loading the dataset via the HuggingFace ``datasets`` library and then
    caches the result locally for future runs.

    Returns
    -------
    pandas.DataFrame
        The complete QM9 dataset as a DataFrame.
    """
    if DEFAULT_RAW_PARQUET.is_file():
        logger.info("Loading QM9 dataset from local cache: %s", DEFAULT_RAW_PARQUET)
        return pd.read_parquet(DEFAULT_RAW_PARQUET)

    logger.info(
        "Local QM9 cache not found – loading from HuggingFace datasets library."
    )
    # ``load_dataset`` returns a ``datasets.Dataset`` object.  Converting it to a
    # DataFrame gives us the familiar pandas API.
    ds = load_dataset("qm9", split="train")  # type: ignore
    df = pd.DataFrame(ds)

    # Ensure the cache directory exists before writing.
    DEFAULT_RAW_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DEFAULT_RAW_PARQUET, index=False)
    logger.info("Cached raw QM9 dataset to %s", DEFAULT_RAW_PARQUET)
    return df


def create_subset(
    *,
    seed: int = DEFAULT_SEED,
    n_samples: int = DEFAULT_SAMPLE_SIZE,
    output_path: Optional[Path] = None,
    raw_path: Optional[Path] = None,
) -> Path:
    """
    Create a reproducible random subset of the QM9 dataset and write it to
    Parquet.

    Parameters
    ----------
    seed : int, optional
        Seed for the random number generator (default ``42``).  The same seed
        always yields the same subset.
    n_samples : int, optional
        Number of molecules to include in the subset (default ``10_000``).
    output_path : pathlib.Path or None, optional
        Destination for the subset file.  If ``None`` the default location
        ``data/processed/molecules_10k.parquet`` is used.
    raw_path : pathlib.Path or None, optional
        Path to a cached raw QM9 Parquet file.  If ``None`` the default
        ``data/raw/qm9.parquet`` is used.

    Returns
    -------
    pathlib.Path
        The path to the written subset file.
    """
    if set_seed is not None:  # pragma: no cover
        set_seed(seed)

    # Ensure deterministic behaviour across NumPy and Python's ``random``.
    np_random = np.random.default_rng(seed)

    # Resolve paths.
    raw_path = Path(raw_path) if raw_path is not None else DEFAULT_RAW_PARQUET
    output_path = Path(output_path) if output_path is not None else DEFAULT_OUTPUT_PARQUET

    # Load the full dataset.
    if raw_path.is_file():
        logger.info("Reading raw QM9 data from %s", raw_path)
        full_df = pd.read_parquet(raw_path)
    else:
        logger.info(
            "Raw QM9 file %s not found – loading via HuggingFace datasets.", raw_path
        )
        full_df = _load_raw_qm9()

    total_rows = len(full_df)
    if n_samples > total_rows:
        raise ValueError(
            f"Requested {n_samples} samples but only {total_rows} rows are available."
        )

    logger.info(
        "Creating a random subset of %d molecules (seed=%d) from %d total rows.",
        n_samples,
        seed,
        total_rows,
    )
    # ``choice`` without replacement gives us a deterministic set of indices.
    subset_indices = np_random.choice(total_rows, size=n_samples, replace=False)
    subset_df = full_df.iloc[subset_indices].reset_index(drop=True)

    # Write the subset.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subset_df.to_parquet(output_path, index=False)
    logger.info("Wrote 10k‑molecule subset to %s", output_path)

    return output_path


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a reproducible 10k‑molecule subset of the QM9 dataset."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed for reproducibility (default: %(default)s).",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=DEFAULT_SAMPLE_SIZE,
        help="Number of molecules to sample (default: %(default)s).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PARQUET,
        help="Path to write the subset Parquet file (default: %(default)s).",
    )
    parser.add_argument(
        "--raw",
        type=Path,
        default=DEFAULT_RAW_PARQUET,
        help="Path to the cached raw QM9 Parquet file (default: %(default)s).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging verbosity (default: %(default)s).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level))
    create_subset(
        seed=args.seed,
        n_samples=args.samples,
        output_path=args.output,
        raw_path=args.raw,
    )


if __name__ == "__main__":
    main()