"""
Download the MoleculeNet Lipophilicity dataset using DeepChem.

This script follows the **verified real data source** specification:
it loads the Lipophilicity (LIPO) dataset via DeepChem's `load_lipo`
function with the 'Raw' featurizer, concatenates the train/valid/test
splits, and writes a CSV containing the canonical ``smiles`` strings
and the experimental ``logP`` values.

The resulting file is stored at ``data/raw/lipophilicity.csv``.
A SHA‑256 checksum of the file is recorded (idempotently) in
``data/checksums.txt`` using the same manifest format expected by the
checksum‑verification script.
"""

import hashlib
import json
import sys
from pathlib import Path

import deepchem as dc
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# Helper: compute SHA‑256 hash of a file
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the hex SHA‑256 hash of ``file_path``."""
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# ----------------------------------------------------------------------
# Helper: read an existing checksum manifest (if any)
# ----------------------------------------------------------------------
def read_checksums(path: Path) -> dict:
    """Parse a ``checksums.txt`` file into ``{relative_path: hash}``."""
    checksums = {}
    if path.is_file():
        with path.open("r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Support both "<hash>  <path>" and "<path>: <hash>"
                if "  " in line:
                    h, p = line.split("  ", 1)
                    checksums[p] = h
                elif ":" in line:
                    p, h = [seg.strip() for seg in line.split(":", 1)]
                    checksums[p] = h
    return checksums

# ----------------------------------------------------------------------
# Helper: write a clean checksum manifest (idempotent)
# ----------------------------------------------------------------------
def write_checksums(path: Path, checksums: dict) -> None:
    """Write ``checksums`` to ``path`` using the canonical format."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for rel_path, h in sorted(checksums.items()):
            f.write(f"{h}  {rel_path}\n")

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    # 1. Load the Lipophilicity dataset via DeepChem
    try:
        tasks, (train, valid, test), transformers = dc.molnet.load_lipo(
            featurizer="Raw"
        )
    except Exception as exc:
        print(f"Failed to load Lipophilicity dataset via DeepChem: {exc}", file=sys.stderr)
        sys.exit(1)

    # 2. Concatenate the three splits (they are already flat arrays)
    X = np.concatenate([train.X, valid.X, test.X]).ravel()
    y = np.concatenate([train.y, valid.y, test.y]).ravel()

    # 3. Build a DataFrame with the required columns
    df = pd.DataFrame({"smiles": X, "logP": y})
    # Ensure there are no NaNs in the target; drop rows where logP is missing
    df = df.dropna(subset=["logP"]).reset_index(drop=True)

    # 4. Write the raw CSV
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "lipophilicity.csv"
    df.to_csv(raw_path, index=False)

    # 5. Record the checksum in the manifest
    checksums_path = Path("data/checksums.txt")
    current = read_checksums(checksums_path)
    current[raw_path.as_posix()] = compute_sha256(raw_path)
    write_checksums(checksums_path, current)

    print(f"Lipophilicity dataset written to {raw_path}")
    print(f"Checksum recorded in {checksums_path}")

if __name__ == "__main__":
    main()
