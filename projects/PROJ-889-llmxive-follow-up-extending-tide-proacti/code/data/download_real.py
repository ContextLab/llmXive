"""
download_real.py
-----------------
Downloads the CodeXGLUE defect‑detection dataset, extracts the source code for each
instance, writes each snippet to a separate ``.py`` file under ``data/raw/real/``,
and creates a SHA‑256 checksum manifest ``data/raw/checksums.txt``.

The script aborts if:
  * The dataset contains fewer than 200 instances.
  * Any written file does not match the checksum recorded in the manifest.

All paths are created via the ``llmxive_toolkit.paths`` helper.
"""

import hashlib
import sys
from pathlib import Path

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


def main() -> None:
    # ------------------------------------------------------------------ #
    # 1. Load the CodeXGLUE defect‑detection dataset
    # ------------------------------------------------------------------ #
    log.info("Loading CodeXGLUE defect‑detection dataset...")
    try:
        dataset = load_dataset("code_x_glue", "defect_detection")
    except Exception as exc:
        log.error(f"Failed to load dataset: {exc}")
        raise

    # Combine all splits (train / validation / test) for a unified count
    total_instances = sum(len(split) for split in dataset.values())
    log.info(f"Dataset loaded – total instances across splits: {total_instances}")

    if total_instances < 200:
        raise RuntimeError(
            f"Dataset contains only {total_instances} instances; "
            "expected at least 200."
        )

    # ------------------------------------------------------------------ #
    # 2. Write each code snippet to a .py file
    # ------------------------------------------------------------------ #
    real_dir = paths.data("raw", "real")
    real_dir.mkdir(parents=True, exist_ok=True)

    checksum_map = {}

    instance_counter = 0
    for split_name, split in dataset.items():
        for idx, record in enumerate(split):
            # The CodeXGLUE defect_detection schema uses the field ``func`` for the code.
            code = record.get("func")
            if not isinstance(code, str):
                # Defensive: skip malformed entries
                log.warning(
                    f"Skipping entry {split_name}[{idx}] – missing 'func' field."
                )
                continue

            # Build a deterministic filename: <split>_<idx>.py
            filename = f"{split_name}_{idx}.py"
            file_path = real_dir / filename

            # Write the source code (ensure a trailing newline)
            file_path.write_text(code.rstrip() + "\n", encoding="utf-8")

            # Compute checksum and store
            checksum = _sha256_of_file(file_path)
            checksum_map[filename] = checksum

            instance_counter += 1

    log.info(f"Wrote {instance_counter} real code files to {real_dir}")

    # ------------------------------------------------------------------ #
    # 3. Write the checksum manifest
    # ------------------------------------------------------------------ #
    checksum_file = paths.data("raw", "checksums.txt")
    with checksum_file.open("w", encoding="utf-8") as fh:
        for fname, chksum in sorted(checksum_map.items()):
            fh.write(f"{chksum}  {fname}\n")
    log.info(f"Checksum manifest written to {checksum_file}")

    # ------------------------------------------------------------------ #
    # 4. Verify manifest integrity – abort on any mismatch
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
        error_msg = "Checksum verification failed for the following files:\n"
        error_msg += "\n".join(f"{fn}: {msg}" for fn, msg in mismatches)
        raise RuntimeError(error_msg)

    log.info("All real files passed checksum verification.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log.exception("download_real.py terminated with an error.")
        sys.exit(1)
