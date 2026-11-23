"""
Data loading utilities for the DFT‑D3 transferability project.
Provides checksum helpers and a loader for the synthetic benchmark
dataset shipped with the repository (data/IL‑Benchmark‑local.zip).
The loader is robust: if the supplied file is a real zip archive it
extracts a CSV named ``pairs.csv``; otherwise it treats the file as a
plain CSV. This satisfies the test suite which only requires the file
to exist and contain the columns ``pair_id`` and ``reference_energy``.
"""

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import zipfile


def calculate_sha256(filepath: Path) -> str:
    """
    Calculate the SHA‑256 checksum of a file.

    Parameters
    ----------
    filepath: Path
        Path to the file whose checksum is required.

    Returns
    -------
    str
        Hex‑encoded SHA‑256 digest.
    """
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_checksums(checksums: Dict[str, str]) -> bool:
    """
    Validate a mapping of file paths (relative to the project root) to
    expected SHA‑256 digests.

    The function returns ``True`` only if *all* files exist and their
    digests match the supplied values. It raises ``FileNotFoundError``
    for missing files and returns ``False`` for mismatches.

    Parameters
    ----------
    checksums: Dict[str, str]
        Mapping of relative file paths to expected SHA‑256 hex strings.

    Returns
    -------
    bool
        ``True`` if every file matches its checksum.
    """
    all_ok = True
    for rel_path, expected in checksums.items():
        path = Path(rel_path)
        if not path.is_file():
            raise FileNotFoundError(f"Checksum validation failed – file not found: {rel_path}")
        actual = calculate_sha256(path)
        if actual != expected:
            all_ok = False
    return all_ok


def load_synthetic_dataset(zip_path: Path) -> Tuple[List[dict], pd.DataFrame]:
    """
    Load the synthetic benchmark dataset shipped with the repository.

    The function is tolerant to the ``zip_path`` being either a genuine
    zip archive (containing a ``pairs.csv`` file) or a plain CSV file
    masquerading as a zip (as used in the test suite). In the latter
    case the CSV is read directly.

    Returns
    -------
    Tuple[List[dict], pd.DataFrame]
        * A list of dictionaries, each with keys ``pair_id`` and
          ``reference_energy``.
        * An (optional) bulk‑properties DataFrame.  The current
          workflow does not require bulk data at this stage, so an
          empty DataFrame is returned when none is found.
    """
    if not zip_path.is_file():
        raise FileNotFoundError(f"Synthetic dataset not found: {zip_path}")

    # Helper to read a CSV from a file‑like object
    def _read_csv_from_bytes(csv_bytes: bytes) -> pd.DataFrame:
        from io import BytesIO

        return pd.read_csv(BytesIO(csv_bytes))

    # Try to treat the file as a zip archive
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Look for a CSV named ``pairs.csv``; fall back to the first CSV we find
            csv_name = None
            for name in zf.namelist():
                if name.lower().endswith(".csv"):
                    if name.lower() == "pairs.csv":
                        csv_name = name
                        break
                    if csv_name is None:
                        csv_name = name
            if csv_name is None:
                raise ValueError("No CSV file found inside the synthetic zip archive.")
            with zf.open(csv_name) as cf:
                pairs_df = pd.read_csv(cf)
    else:
        # Not a zip – assume the file itself is a CSV
        pairs_df = pd.read_csv(zip_path)

    # Basic validation
    required = {"pair_id", "reference_energy"}
    missing = required.difference(pairs_df.columns)
    if missing:
        raise ValueError(f"Synthetic pairs CSV is missing required columns: {missing}")

    # Convert to list of dicts
    pairs = pairs_df.to_dict(orient="records")

    # Attempt to load a bulk‑properties CSV if it exists inside the archive
    bulk_df = pd.DataFrame()
    if zipfile.is_zipfile(zip_path):
        with zipfile.ZipFile(zip_path, "r") as zf:
            bulk_name = None
            for name in zf.namelist():
                if name.lower().endswith("bulk_properties.csv"):
                    bulk_name = name
                    break
            if bulk_name:
                with zf.open(bulk_name) as bf:
                    bulk_df = pd.read_csv(bf)

    return pairs, bulk_df


def main() -> None:
    """
    Simple command‑line entry point useful for manual inspection.
    Prints a summary of the synthetic dataset.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Inspect the synthetic IL benchmark dataset.")
    parser.add_argument(
        "path",
        type=Path,
        help="Path to the synthetic dataset (zip or CSV).",
    )
    args = parser.parse_args()

    pairs, bulk = load_synthetic_dataset(args.path)
    print(f"Loaded {len(pairs)} ion‑pair entries.")
    if not bulk.empty:
        print(f"Bulk properties table shape: {bulk.shape}")
    else:
        print("No bulk properties table found.")
