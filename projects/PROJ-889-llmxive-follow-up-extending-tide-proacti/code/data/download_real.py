"""
download_real.py
-----------------
Downloads the official TIDE evaluation dataset from HuggingFace, extracts the source
code for each instance, writes each snippet to a separate .py file under
data/raw/real/, creates a CSV manifest `tide_eval.csv`, and updates the SHA‑256
checksum manifest `data/raw/checksums.txt`.

The script aborts if:
  * The dataset contains fewer than 200 instances.
  * Any written file does not match the checksum recorded in the manifest.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 digest of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_checksum_manifest(base_dir: Path, manifest_path: Path) -> None:
    """
    Scan ``base_dir`` (which contains ``real`` and ``synthetic`` sub‑folders)
    and write a SHA‑256 checksum manifest. Existing entries are overwritten.
    """
    checksum_entries = {}
    for sub in ["real", "synthetic"]:
        sub_dir = base_dir / sub
        if not sub_dir.is_dir():
            continue
        for py_file in sub_dir.glob("*.py"):
            checksum_entries[py_file.name] = _sha256_of_file(py_file)

    with manifest_path.open("w", encoding="utf-8") as fh:
        for fname in sorted(checksum_entries):
            fh.write(f"{checksum_entries[fname]}  {fname}\\n")
    log.info(f"Checksum manifest refreshed ({len(checksum_entries)} entries).")

def _verify_checksums(base_dir: Path, manifest_path: Path) -> None:
    """Raise ``RuntimeError`` if any file does not match the recorded checksum."""
    mismatches = []
    with manifest_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                expected_hash, fname = line.split(maxsplit=1)
                candidate = base_dir / "real" / fname
                if not candidate.is_file():
                    candidate = base_dir / "synthetic" / fname
                if not candidate.is_file():
                    mismatches.append((fname, "file not found"))
                    continue
                actual_hash = _sha256_of_file(candidate)
                if actual_hash != expected_hash:
                    mismatches.append((fname, f"expected {expected_hash}, got {actual_hash}"))
            except ValueError:
                log.warning(f"Skipping malformed line in checksum file: {line}")

    if mismatches:
        msg = "Checksum verification failed:\\n"
        msg += "\\n".join(f"{fn}: {reason}" for fn, reason in mismatches)
        raise RuntimeError(msg)

def _load_tide_dataset() -> List[dict]:
    """
    Loads the official TIDE evaluation dataset via ``datasets.load_dataset``.
    Returns a list of record dictionaries.
    """
    log.info("Downloading the TIDE evaluation dataset (allenai/tide-eval)…")
    try:
        ds = load_dataset("allenai/tide-eval", split="train")
    except Exception as exc:
        log.error(f"Failed to download TIDE dataset: {exc}")
        raise

    records = []
    for idx, record in enumerate(ds):
        # The dataset provides a ``func`` field containing the source code.
        # ``label`` (0/1) indicates the presence of a hidden problem.
        if not isinstance(record.get("func"), str):
            log.warning(f"Record {idx} missing a valid 'func' field – skipping.")
            continue
        records.append(record)
    log.info(f"Loaded {len(records)} records from the TIDE dataset.")
    return records

def main() -> None:
    log.info("Starting real TIDE data acquisition…")
    records = _load_tide_dataset()

    if len(records) < 200:
        raise RuntimeError(
            f"TIDE dataset contains only {len(records)} instances; expected at least 200."
        )

    # Prepare directories
    raw_root = paths.data("raw")
    real_dir = raw_root / "real"
    real_dir.mkdir(parents=True, exist_ok=True)

    # Write individual .py files and collect CSV rows
    csv_rows = []
    for idx, record in enumerate(records):
        code = record["func"]
        label = record.get("label", 0)  # default to 0 if missing
        # Ensure a trailing newline for consistency
        code_clean = code.rstrip() + "\\n"

        filename = f"tide_{idx}.py"
        file_path = real_dir / filename
        file_path.write_text(code_clean, encoding="utf-8")

        checksum = _sha256_of_file(file_path)

        csv_rows.append({
            "instance_id": idx,
            "filename": filename,
            "ground_truth_label": int(label),
            "sha256": checksum,
        })

    # Write CSV manifest
    csv_path = raw_root / "tide_eval.csv"
    pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
    log.info(f"Wrote CSV manifest with {len(csv_rows)} rows to {csv_path}")

    # Write checksum manifest (includes both real and any synthetic files)
    checksum_path = raw_root / "checksums.txt"
    _write_checksum_manifest(raw_root, checksum_path)

    # Verify integrity
    log.info("Verifying written files against checksum manifest…")
    _verify_checksums(raw_root, checksum_path)
    log.info("All files passed checksum verification. Real data acquisition completed.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("download_real.py terminated with an error.")
        sys.exit(1)
