"""
acquire_real.py
----------------
Downloads the official TIDE evaluation dataset from the HuggingFace hub without
depending on the heavy `datasets` library (which pulls in `pyarrow` and fails
with the available NumPy version). The script extracts each code snippet to a
separate ``.py`` file under ``data/raw/real/``, writes a CSV manifest
``tide_eval.csv`` and creates a SHA‑256 checksum manifest ``checksums.txt``.
"""

import json
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 digest of *file_path*."""
    import hashlib

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

def _load_tide_dataset() -> list[dict]:
    """
    Download the raw JSONL file for the TIDE evaluation dataset from the
    HuggingFace hub and parse it into a list of dictionaries.
    """
    log.info("Downloading TIDE dataset from HuggingFace hub (allenai/tide-eval)…")
    # The repository contains a file ``train.jsonl`` with the records.
    # If the filename changes, this will raise and surface the problem.
    try:
        file_path = hf_hub_download(repo_id="allenai/tide-eval", filename="train.jsonl")
    except Exception as exc:
        log.error(f"Failed to download TIDE dataset file: {exc}")
        raise

    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                log.warning(f"Skipping malformed JSON line: {e}")
    log.info(f"Loaded {len(records)} records from the TIDE dataset.")
    return records

def main() -> None:
    """Run the real TIDE data acquisition process."""
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
        code = record.get("func")
        label = record.get("label", 0)  # default to 0 if missing
        if not isinstance(code, str):
            log.warning(f"Record {idx} missing a valid 'func' field – skipping.")
            continue
        # Ensure a trailing newline for consistency
        code_clean = code.rstrip() + "\n"

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
    import pandas as pd

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
        log.exception("acquire_real.py terminated with an error.")
        sys.exit(1)
