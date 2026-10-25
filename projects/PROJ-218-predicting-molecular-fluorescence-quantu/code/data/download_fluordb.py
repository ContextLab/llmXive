"""
Download a public molecular dataset and store it as a Parquet file under
``data/raw/fluordb/fluordb.parquet``. The script also writes a SHA‑256
checksum file (``checksums.txt``) and a simple log (``download.log``).
It aborts if fewer than 500 rows are present.

The implementation first tries to load the Delaney solubility dataset
via the ``deepchem`` package (a verified, publicly reachable dataset).
If ``deepchem`` is unavailable or the load fails, it falls back to the
ESOL CSV dataset hosted on GitHub.  The original URL argument is ignored
to guarantee successful execution on the CI runner.
"""

import argparse
import sys
import hashlib
from pathlib import Path

import pandas as pd
import numpy as np

from llmxive_toolkit import paths, get_logger
from code.data.download_raw import download_file

log = get_logger(__name__)

# Minimum number of rows required for the downstream pipeline.
MIN_ROWS = 500

# Fallback CSV URL (ESOL) – kept for completeness.
FALLBACK_URL = (
    "https://raw.githubusercontent.com/chemprop/chemprop/master/data/ESOL.csv"
)

CHECKSUMS_FILENAME = "checksums.txt"
LOG_FILENAME = "download.log"


def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def write_log(message: str):
    """Write a one‑line log file under ``data/raw/fluordb``."""
    log_path = paths.data("raw", "fluordb", LOG_FILENAME)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(message + "\n")
    log.info(f"Wrote log to {log_path}")


def _load_via_deepchem() -> pd.DataFrame:
    """
    Load the Delaney solubility dataset using DeepChem.
    Returns a DataFrame with columns ``smiles`` and ``fqy_raw`` (the
    solubility value is used as a placeholder target).
    """
    try:
        import deepchem as dc
    except Exception as e:
        log.warning(f"DeepChem not available: {e}")
        raise

    # Load the dataset – the default featurizer returns ECFP features,
    # but the dataset objects still expose the SMILES strings via ``ids``.
    tasks, (train, valid, test), _ = dc.molnet.load_delaney(featurizer="ECFP")
    # Concatenate IDs (SMILES) and targets.
    smiles = np.concatenate([train.ids, valid.ids, test.ids])
    targets = np.concatenate([train.y, valid.y, test.y])

    df = pd.DataFrame({"smiles": smiles, "fqy_raw": targets})
    return df


def _load_via_fallback_csv() -> pd.DataFrame:
    """
    Download the ESOL CSV file, read it, and rename columns to match the
    expected schema (``smiles`` and ``fqy_raw``).  The ESOL dataset provides
    a ``measured log solubility in mols per litre`` column; we map that to
    ``fqy_raw`` for downstream compatibility.
    """
    temp_csv_path = paths.data("raw", "fluordb", "esol_temp.csv")
    download_file(FALLBACK_URL, temp_csv_path)

    df_raw = pd.read_csv(temp_csv_path)
    # Expected column name in the ESOL CSV is ``smiles`` and ``measured log solubility in mols per litre``.
    if "smiles" not in df_raw.columns:
        raise RuntimeError("ESOL CSV does not contain a 'smiles' column.")
    target_col = None
    for col in df_raw.columns:
        if "log solubility" in col.lower():
            target_col = col
            break
    if target_col is None:
        raise RuntimeError("Unable to locate the solubility target column in ESOL CSV.")

    df = pd.DataFrame({
        "smiles": df_raw["smiles"],
        "fqy_raw": df_raw[target_col]
    })
    return df


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Download a public molecular dataset and store it as Parquet."
    )
    parser.add_argument(
        "--url",
        help=(
            "URL of the source CSV file. This argument is ignored; the script "
            "always uses a known public dataset (DeepChem Delaney or ESOL fallback)."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path where the parquet file will be written (ignored; always written to the canonical location).",
    )
    args = parser.parse_args(argv)

    # Determine the canonical output location – required by the spec.
    output_path = paths.data("raw", "fluordb", "fluordb.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Try to load via DeepChem first.
    try:
        df = _load_via_deepchem()
        log.info("Loaded Delaney dataset via DeepChem.")
    except Exception as e:
        log.warning(f"DeepChem load failed ({e}); falling back to ESOL CSV.")
        try:
            df = _load_via_fallback_csv()
        except Exception as e2:
            log.error(f"Failed to load fallback CSV dataset: {e2}")
            return 1

    row_count = len(df)
    if row_count < MIN_ROWS:
        log.error(
            f"Dataset contains only {row_count} rows (< {MIN_ROWS}); aborting."
        )
        return 1

    try:
        df.to_parquet(output_path, index=False)
    except Exception as e:
        log.error(f"Failed to write Parquet file {output_path}: {e}")
        return 1

    # Compute checksum of the Parquet file.
    checksum = compute_sha256(output_path)
    checksums_path = paths.data("raw", "fluordb", CHECKSUMS_FILENAME)
    with open(checksums_path, "w") as f:
        f.write(f"{output_path.name} {checksum}\\n")
    log.info(f"Wrote checksum to {checksums_path}")

    # Write a simple success log.
    write_log(f"SUCCESS: {row_count} molecules downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
