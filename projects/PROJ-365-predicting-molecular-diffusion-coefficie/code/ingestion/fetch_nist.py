"""
fetch_nist.py
----------------
Retrieve experimental diffusion data from the NIST Thermodynamics Research
Center (TRC) using the ``thermo`` package.

The script attempts to download the dataset via the helper function
:func:`fetch_from_nist` defined in ``code/ingestion/fetch_real.py``.  If the
download succeeds, the resulting CSV is stored under ``data/raw/`` and a
source‑flag JSON file is written indicating a *real* data source.

If any exception occurs (e.g., network failure, missing API key, etc.),
the script falls back to the synthetic data generator defined in
``code/ingestion/verify_plan_and_fallback.py`` (task T007b).  The fallback
writes a synthetic CSV to the same location and records a *synthetic*
source flag.

The module provides a ``main`` entry‑point so it can be executed directly:

    python code/ingestion/fetch_nist.py
"""

import sys
from pathlib import Path

# Functions that handle the real download
from ingestion.fetch_real import (
    ensure_output_dir,
    fetch_from_nist,
)

# Functions that handle the synthetic fallback and source‑flag recording
from ingestion.verify_plan_and_fallback import (
    run_synthetic_fallback,
    write_source_flag,
)

# Logging utilities
from utils.logging import get_logger, log_error, log_info

def _download_real_data(output_dir: Path) -> Path:
    """
    Attempt to download the experimental diffusion dataset from NIST.

    Parameters
    ----------
    output_dir: Path
        Directory where the CSV should be written.  The helper
        ``fetch_from_nist`` is expected to create the file inside this
        directory and return the full path to the written CSV.

    Returns
    -------
    Path
        Path to the downloaded CSV file.

    Raises
    ------
    Exception
        Propagates any exception raised by ``fetch_from_nist`` so that the
        caller can decide whether to fall back to synthetic data.
    """
    # ``fetch_from_nist`` is part of the existing code base and is
    # responsible for the actual interaction with the ``thermo`` package.
    # It returns the absolute path to the created CSV file.
    csv_path = fetch_from_nist()
    return csv_path

def _fallback_to_synthetic(output_dir: Path) -> Path:
    """
    Generate a synthetic diffusion dataset using the fallback routine.

    Parameters
    ----------
    output_dir: Path
        Directory where the synthetic CSV will be stored.  The fallback
        routine respects the same contract as ``fetch_from_nist`` and
        returns the path to the generated file.

    Returns
    -------
    Path
        Path to the synthetic CSV file.
    """
    synthetic_path = run_synthetic_fallback()
    return synthetic_path

def main() -> None:
    """
    Orchestrates the data acquisition process.

    1. Ensure ``data/raw`` exists.
    2. Try to fetch the real NIST dataset.
    3. On failure, generate a synthetic dataset.
    4. Write a ``data_source_flag.json`` file indicating the origin.
    """
    logger = get_logger(__name__)

    # Step 1 – make sure the output directory exists
    raw_dir = Path("data/raw")
    try:
        ensure_output_dir(raw_dir)
    except Exception as exc:
        log_error(logger, f"Could not create raw data directory '{raw_dir}': {exc}")
        sys.exit(1)

    # Step 2 – attempt the real download
    try:
        csv_path = _download_real_data(raw_dir)
        log_info(logger, f"NIST diffusion data successfully fetched to '{csv_path}'.")
        write_source_flag("real")
    except Exception as exc:
        # Any problem here triggers the synthetic fallback
        log_error(logger, f"Failed to fetch NIST data: {exc}")
        log_info(logger, "Falling back to synthetic data generation (T007b).")
        try:
            csv_path = _fallback_to_synthetic(raw_dir)
            log_info(logger, f"Synthetic diffusion data generated at '{csv_path}'.")
            write_source_flag("synthetic")
        except Exception as fallback_exc:
            # If the fallback also fails we cannot continue – surface the error.
            log_error(
                logger,
                f"Synthetic fallback also failed: {fallback_exc}",
            )
            sys.exit(1)

if __name__ == "__main__":
    main()