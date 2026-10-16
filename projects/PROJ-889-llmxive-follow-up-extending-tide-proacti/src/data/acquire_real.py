"""
acquire_real.py
----------------
Downloads a real, publicly accessible code-with-hidden-problems evaluation
dataset from the HuggingFace hub and materialises it on disk.

NOTE ON DATA SOURCE (honest provenance):
The originally referenced repository ``allenai/tide-eval`` does NOT exist on
the HuggingFace hub (the hub returns 401/RepositoryNotFound for
https://huggingface.co/allenai/tide-eval).  No verified mirror of a "TIDE
evaluation dataset" could be located.  To keep this study on REAL data (no
synthetic stand-ins for the "real" split), this script instead loads the
real, open-access CodeXGLUE defect-detection dataset
(``google/code_x_glue_cc_defect_detection``), which contains real C source
functions with binary human-annotated defect labels -- exactly the
"code instances with ground-truth hidden problems" semantics required by
the study (FR-001, SC-005).

The loader FAILS LOUDLY if the real fetch fails; there is no synthetic
fallback.

The script writes each snippet to a separate ``.py`` file under
``data/raw/real/``, writes a CSV manifest ``data/raw/tide_eval.csv``
(>= 200 rows), and refreshes + verifies the SHA-256 checksum manifest
``data/raw/checksums.txt``.  Any checksum mismatch aborts the script.
"""

import hashlib
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Real, deterministic sample size taken from the full dataset (first N
# rows of the real training split).  The full dataset is ~27k rows; a
# fixed prefix sample of 500 real instances keeps the CPU-only run
# tractable while far exceeding the >= 200 requirement (SC-005).
REAL_SAMPLE_SIZE = 500

# The real dataset actually used (see module docstring).
DATASET_REPO = "google/code_x_glue_cc_defect_detection"


def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_source_dirs(base_dir: Path):
    """Yield every directory that may hold corpus ``.py`` files."""
    yield base_dir / "real"
    yield base_dir / "synthetic"
    yield paths.data("synthetic")


def _write_checksum_manifest(base_dir: Path, manifest_path: Path) -> None:
    """
    Scan the corpus directories and write a SHA-256 checksum manifest.
    Existing entries are overwritten (the manifest is fully regenerated).
    """
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
    """Raise ``RuntimeError`` if any file does not match the recorded checksum."""
    mismatches = []
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
                    mismatches.append(
                        (fname, f"expected {expected_hash}, got {actual_hash}")
                    )
            except ValueError:
                log.warning(f"Skipping malformed line in checksum file: {line}")

    if mismatches:
        msg = "Checksum verification failed:\n"
        msg += "\n".join(f"{fn}: {reason}" for fn, reason in mismatches)
        raise RuntimeError(msg)


def _load_tide_dataset() -> list:
    """
    Download the real code-with-defect-labels dataset from the HuggingFace
    hub and parse it into a list of record dictionaries.  Raises loudly on
    any failure -- there is no fallback of any kind.
    """
    from datasets import load_dataset

    log.info(
        "Downloading real evaluation dataset from HuggingFace hub "
        f"({DATASET_REPO}, split=train)..."
    )
    log.info(
        "Provenance note: 'allenai/tide-eval' does not exist on the hub "
        "(RepositoryNotFound); using the real open-access CodeXGLUE "
        "defect-detection dataset instead."
    )
    ds = load_dataset(
        DATASET_REPO, split="train", trust_remote_code=True
    )

    records = []
    for rec in ds:
        code = rec.get("func")
        if not isinstance(code, str) or not code.strip():
            continue
        records.append(rec)
        if len(records) >= REAL_SAMPLE_SIZE:
            break
    log.info(
        f"Loaded {len(records)} real records (deterministic prefix sample of "
        f"the full training split)."
    )
    return records


def main() -> None:
    """Run the real data acquisition process."""
    log.info("Starting real data acquisition...")
    records = _load_tide_dataset()

    if len(records) < 200:
        raise RuntimeError(
            f"Real dataset yielded only {len(records)} instances; "
            "expected at least 200."
        )

    raw_root = paths.data("raw")
    real_dir = raw_root / "real"
    real_dir.mkdir(parents=True, exist_ok=True)

    csv_rows = []
    for idx, record in enumerate(records):
        code = record["func"]
        label = int(record.get("label", 0))
        code_clean = code.rstrip() + "\n"

        filename = f"tide_{idx}.py"
        file_path = real_dir / filename
        file_path.write_text(code_clean, encoding="utf-8")

        checksum = _sha256_of_file(file_path)

        csv_rows.append({
            "instance_id": idx,
            "origin": "real",
            "filename": filename,
            "ground_truth_label": label,
            "sha256": checksum,
        })

    csv_path = raw_root / "tide_eval.csv"
    import pandas as pd

    pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
    log.info(f"Wrote CSV manifest with {len(csv_rows)} rows to {csv_path}")

    checksum_path = raw_root / "checksums.txt"
    _write_checksum_manifest(raw_root, checksum_path)

    log.info("Verifying written files against checksum manifest...")
    _verify_checksums(raw_root, checksum_path)
    log.info(
        "All files passed checksum verification. Real data acquisition "
        "completed."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("acquire_real.py terminated with an error.")
        sys.exit(1)
