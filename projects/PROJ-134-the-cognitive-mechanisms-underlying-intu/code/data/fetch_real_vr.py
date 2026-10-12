"""
Real VR Log Ingestion (T092)

This script fetches real VR interaction logs from the verified HuggingFace dataset
``moral-foundations/vr-logs-v`` and writes the result to ``data/raw/vr_logs_real.parquet``.
If the fetch fails (network error, 404, etc.) the script raises
``RealDataUnavailableError`` with the mandated error message, satisfying FR‑006
"fail loudly" semantics.

Usage:
    python code/data/fetch_real_vr.py [--output <path>]

The ``--output`` argument overrides the default output location.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from datasets import load_dataset, DatasetDict  # huggingface_hub datasets library

from code.config import get_path
from code.data.exceptions import RealDataUnavailableError

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
DEFAULT_OUTPUT_REL = "data/raw/vr_logs_real.parquet"
HF_DATASET_ID = "moral-foundations/vr-logs-v"  # verified source for VR logs

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def fetch_real_vr_logs(output_path: Optional[Path] = None) -> Path:
    """
    Download the real VR logs dataset and write it to Parquet.

    Parameters
    ----------
    output_path: Optional[Path]
        Destination path. If ``None`` the default location
        ``data/raw/vr_logs_real.parquet`` (relative to the project root) is used.

    Returns
    -------
    Path
        The absolute path to the written Parquet file.

    Raises
    ------
    RealDataUnavailableError
        If the dataset cannot be fetched for any reason.
    """
    # Resolve output path
    if output_path is None:
        output_path = get_path(DEFAULT_OUTPUT_REL)
    else:
        # ``output_path`` may be a string; convert using ``get_path`` for consistency
        output_path = get_path(str(output_path))

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # ``load_dataset`` returns a ``DatasetDict``; we expect a single split (e.g., "train")
        dataset: DatasetDict = load_dataset(HF_DATASET_ID)
    except Exception as exc:
        # Propagate a clear, spec‑compliant error
        raise RealDataUnavailableError(
            "FR-006 Violation: Real VR logs missing. Fetch failed."
        ) from exc

    # Convert to pandas DataFrame – this works for both arrow‑backed and regular datasets
    try:
        # Prefer the first split available
        first_split = next(iter(dataset.values()))
        df: pd.DataFrame = first_split.to_pandas()
    except Exception as exc:
        raise RealDataUnavailableError(
            "FR-006 Violation: Real VR logs missing. Fetch failed."
        ) from exc

    # Write to Parquet
    try:
        df.to_parquet(output_path, index=False)
    except Exception as exc:
        raise RealDataUnavailableError(
            "FR-006 Violation: Real VR logs missing. Fetch failed."
        ) from exc

    return output_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch real VR interaction logs (T092) and store them as Parquet."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output path (relative to project root). "
             f"Defaults to '{DEFAULT_OUTPUT_REL}'."
    )
    return parser.parse_args()

def main() -> int:
    args = _parse_cli()
    try:
        out_path = fetch_real_vr_logs(args.output)
        print(f"VR logs successfully written to: {out_path}", file=sys.stdout)
        return 0
    except RealDataUnavailableError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        # Unexpected errors are re‑raised to make debugging visible
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    sys.exit(main())
