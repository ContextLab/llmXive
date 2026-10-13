"""
download_real.py
-----------------
Downloads the CodeXGLUE defect‑detection dataset, extracts the source code for each
instance, writes each snippet to a separate ``.py`` file under ``data/raw/real/``,
and creates a SHA‑256 checksum manifest ``data/raw/checksums.txt``.

The script aborts if:
  * The dataset contains fewer than 200 instances.
  * Any written file does not match the checksum recorded in the manifest.

It first attempts to load the dataset via the ``datasets`` library. If that fails
(e.g., due to a missing ``pyarrow`` dependency), it falls back to downloading the
raw JSONL files directly from the HuggingFace Hub using ``huggingface_hub``.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------- #
# Helper: SHA‑256 checksum of a file
# ---------------------------------------------------------------------- #
def _sha256_of_file(file_path: Path) -> str:
    """Return the hexadecimal SHA‑256 digest of *file_path*."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# ---------------------------------------------------------------------- #
# Fallback loader: download raw JSONL files from the Hub
# ---------------------------------------------------------------------- #
def _load_via_hf_hub() -> List[Tuple[str, List[dict]]]:
    """
    Returns a list of (split_name, records) tuples for the three splits.
    Each record is the raw JSON object from the dataset; we only need the
    ``func`` field which contains the source code.
    """
    try:
        from huggingface_hub import hf_hub_download
    except Exception as exc:
        log.error(f"Failed to import huggingface_hub: {exc}")
        raise

    repo_id = "code_x_glue/defect_detection"
    splits = ["train", "validation", "test"]
    result = []
    for split in splits:
        filename = f"{split}.jsonl"
        log.info(f"Downloading {filename} from the HuggingFace Hub...")
        file_path = hf_hub_download(repo_id=repo_id, filename=filename)
        records: List[dict] = []
        with open(file_path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError as jde:
                        log.warning(f"Skipping malformed line in {filename}: {jde}")
        result.append((split, records))
    return result

# ---------------------------------------------------------------------- #
# Primary loader: try the ``datasets`` library first
# ---------------------------------------------------------------------- #
def _load_dataset() -> List[Tuple[str, List[dict]]]:
    """
    Attempts to load the dataset via ``datasets.load_dataset``.
    If that raises any exception (commonly due to missing ``pyarrow``),
    falls back to the Hub downloader.
    """
    try:
        from datasets import load_dataset
        log.info("Attempting to load dataset via the 'datasets' library...")
        ds = load_dataset("code_x_glue", "defect_detection")
        splits = []
        for split_name, split in ds.items():
            # ``split`` is a Dataset object; we can convert to a list of dicts.
            splits.append((split_name, list(split)))
        return splits
    except Exception as exc:
        log.warning(f"Loading via 'datasets' failed ({exc}); using fallback method.")
        return _load_via_hf_hub()

# ---------------------------------------------------------------------- #
# Main routine
# ---------------------------------------------------------------------- #
def main() -> None:
    log.info("Loading CodeXGLUE defect‑detection dataset...")
    dataset_splits = _load_dataset()

    total_instances = sum(len(records) for _, records in dataset_splits)
    log.info(f"Dataset loaded – total instances across splits: {total_instances}")

    if total_instances < 200:
        raise RuntimeError(
            f"Dataset contains only {total_instances} instances; "
            "expected at least 200."
        )

    real_dir = paths.data("raw", "real")
    real_dir.mkdir(parents=True, exist_ok=True)

    checksum_map = {}
    instance_counter = 0

    for split_name, records in dataset_splits:
        for idx, record in enumerate(records):
            code = record.get("func")
            if not isinstance(code, str):
                log.warning(
                    f"Skipping entry {split_name}[{idx}] – missing or non‑string 'func' field."
                )
                continue

            filename = f"{split_name}_{idx}.py"
            file_path = real_dir / filename
            file_path.write_text(code.rstrip() + "\n", encoding="utf-8")

            checksum = _sha256_of_file(file_path)
            checksum_map[filename] = checksum
            instance_counter += 1

    log.info(f"Wrote {instance_counter} real code files to {real_dir}")

    # ------------------------------------------------------------------ #
    # Write checksum manifest
    # ------------------------------------------------------------------ #
    checksum_file = paths.data("raw", "checksums.txt")
    with checksum_file.open("w", encoding="utf-8") as fh:
        for fname, chksum in sorted(checksum_map.items()):
            fh.write(f"{chksum}  {fname}\\n")
    log.info(f"Checksum manifest written to {checksum_file}")

    # ------------------------------------------------------------------ #
    # Verify manifest integrity – abort on any mismatch
    # ------------------------------------------------------------------ #
    log.info("Verifying written files against checksum manifest...")
    mismatches = []
    with checksum_file.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            expected_hash, fname = line.split(maxsplit=1)
            target_path = real_dir / fname
            if not target_path.is_file():
                mismatches.append((fname, "missing file"))
                continue
            actual_hash = _sha256_of_file(target_path)
            if actual_hash != expected_hash:
                mismatches.append((fname, f"expected {expected_hash}, got {actual_hash}"))

    if mismatches:
        error_msg = "Checksum verification failed for the following files:\\n"
        error_msg += "\\n".join(f"{fn}: {msg}" for fn, msg in mismatches)
        raise RuntimeError(error_msg)

    log.info("All real files passed checksum verification.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("download_real.py terminated with an error.")
        sys.exit(1)
