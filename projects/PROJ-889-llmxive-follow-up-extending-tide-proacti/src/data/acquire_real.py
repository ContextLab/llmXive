"""
acquire_real.py
----------------
Downloads the official TIDE evaluation dataset via the `datasets` library
and materializes it on disk as individual .py files and a manifest CSV.
"""

import hashlib
import sys
from pathlib import Path
import pandas as pd
import datasets
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Sample size to keep the run tractable while satisfying SC-005 (>= 200).
REAL_SAMPLE_SIZE = 500
DATASET_ID = "allenai/tide-eval"

def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _iter_source_dirs(base_dir: Path):
    """Yield every directory that may hold corpus .py files."""
    yield base_dir / "real"
    yield paths.data("synthetic")

def _write_checksum_manifest(base_dir: Path, manifest_path: Path) -> None:
    """Scan the corpus directories and write a SHA-256 checksum manifest."""
    checksum_entries = {}
    for sub_dir in _iter_source_dirs(base_dir):
        if not sub_dir.is_dir():
            continue
        for py_file in sub_dir.glob("*.py"):
            checksum_entries[py_file.name] = _sha256_of_file(py_file)

    with manifest_path.open("w", encoding="utf-8") as fh:
        for fname in sorted(checksum_entries):
            fh.write(f"{checksum_entries[fname]}  {fname}\n")
    log.info(f"Checksum manifest refreshed ({len(checksum_entries)} entries).")

def _verify_checksums(base_dir: Path, manifest_path: Path) -> None:
    """Raise RuntimeError if any file does not match the recorded checksum."""
    mismatches = []
    if not manifest_path.exists():
        return
    with manifest_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                expected_hash, fname = line.split(maxsplit=1)
                candidate = None
                for sub_dir in _iter_source_dirs(base_dir):
                    maybe = sub_dir / fname
                    if maybe.is_file():
                        candidate = maybe
                        break
                if candidate is None:
                    mismatches.append((fname, "file not found"))
                    continue
                actual_hash = _sha256_of_file(candidate)
                if actual_hash != expected_hash:
                    mismatches.append((fname, f"expected {expected_hash}, got {actual_hash}"))
            except ValueError:
                log.warning(f"Skipping malformed line in checksum file: {line}")

    if mismatches:
        msg = "Checksum verification failed:\n"
        msg += "\n".join(f"{fn}: {reason}" for fn, reason in mismatches)
        raise RuntimeError(msg)

def main() -> None:
    """Run the real data acquisition process."""
    log.info(f"Loading real evaluation dataset from HuggingFace: {DATASET_ID}...")
    try:
        # Load the dataset. Use 'test' split if available, else 'train'.
        ds_dict = datasets.load_dataset(DATASET_ID)
        split = 'test' if 'test' in ds_dict else 'train'
        dataset = ds_dict[split]
    except Exception as e:
        log.error(f"Failed to load dataset {DATASET_ID}: {e}")
        sys.exit(1)

    records = []
    # The TIDE dataset usually contains 'code' (or 'func') and 'label'.
    for i in range(min(len(dataset), REAL_SAMPLE_SIZE)):
        row = dataset[i]
        code = row.get("code") or row.get("func")
        label = row.get("label")
        if code is None:
            continue
        records.append({"func": str(code), "label": int(label) if label is not None else 0})

    if len(records) < 200:
        raise RuntimeError(f"Real dataset yielded only {len(records)} instances; expected >= 200.")

    raw_root = paths.data("raw")
    real_dir = raw_root / "real"
    real_dir.mkdir(parents=True, exist_ok=True)

    csv_rows = []
    for idx, record in enumerate(records):
        code_clean = record["func"].rstrip() + "\n"
        filename = f"tide_{idx}.py"
        file_path = real_dir / filename
        file_path.write_text(code_clean, encoding="utf-8")
        
        csv_rows.append({
            "instance_id": idx,
            "origin": "real",
            "filename": filename,
            "ground_truth_label": record["label"],
            "sha256": _sha256_of_file(file_path),
        })

    csv_path = raw_root / "tide_eval.csv"
    pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
    log.info(f"Wrote CSV manifest with {len(csv_rows)} rows to {csv_path}")

    # Checksums are managed globally across real and synthetic. 
    # We write it here, but generate_synthetic will refresh it.
    checksum_path = raw_root / "checksums.txt"
    _write_checksum_manifest(raw_root, checksum_path)
    _verify_checksums(raw_root, checksum_path)
    log.info("Real data acquisition completed successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("acquire_real.py terminated with an error.")
        sys.exit(1)
