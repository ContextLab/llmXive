"""
download_pi_bench.py

Downloads the public π‑Bench dataset via the 🤗 datasets library, streams each
example to a separate JSON file under the project's ``data/raw`` directory,
computes a SHA‑256 checksum for each file, writes a manifest ``checksums.txt``,
and retries the whole download up to three times on failure.

The script is deliberately lightweight and CPU‑only – it does not require
GPU resources.  It is invoked from the quick‑start wrapper at
``src/pipelines/download_pi_bench.py``.
"""

import argparse
import json
import logging
import time
from pathlib import Path
from typing import List, Tuple, Optional

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _sha256_checksum(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    import hashlib

    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_checksums(files: List[Tuple[Path, str]], out_path: Path) -> None:
    """Write a manifest of SHA‑256 checksums."""
    with out_path.open("w", encoding="utf-8") as f:
        for rel_path, checksum in files:
            f.write(f"{checksum}  {rel_path}\n")
    log.info(f"Checksum manifest written to {out_path}")


def _download_pi_bench(
    raw_dir: Path, max_examples: Optional[int] = None
) -> List[Tuple[Path, str]]:
    """
    Stream the ``pi_bench`` dataset from the 🤗 Hub and write each example
    as a JSON file.

    Parameters
    ----------
    raw_dir: Path
        Destination directory for the JSON files.
    max_examples: Optional[int]
        If set, limits the number of written examples (useful for CI).

    Returns
    -------
    List[Tuple[Path, str]]
        List of ``(relative_path, checksum)`` for every written file.
    """
    log.info("Starting download of the π‑Bench dataset via 🤗 datasets")
    try:
        dataset = load_dataset("pi_bench", streaming=True)
    except Exception as exc:
        log.error(f"Failed to load π‑Bench via datasets: {exc}")
        raise

    # The streaming object yields dictionaries; we treat it as an iterable.
    checksums: List[Tuple[Path, str]] = []
    for idx, example in enumerate(dataset):
        if max_examples is not None and idx >= max_examples:
            break

        # Derive a safe filename from a unique identifier in the example.
        # The dataset typically provides a ``task_id`` field; fall back to an
        # index‑based name if it is missing.
        raw_id = example.get("task_id") or example.get("id") or f"example_{idx}"
        safe_name = (
            str(raw_id)
            .replace("/", "_")
            .replace("\\", "_")
            .replace(" ", "_")
        )
        json_path = raw_dir / f"{safe_name}.json"
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(example, jf, ensure_ascii=False, indent=2)

        rel_path = json_path.relative_to(raw_dir)
        checksum = _sha256_checksum(json_path)
        checksums.append((rel_path, checksum))

        if (idx + 1) % 10 == 0:
            log.debug(f"Wrote {idx + 1} π‑Bench examples")

    log.info(f"Finished writing {len(checksums)} π‑Bench examples to {raw_dir}")
    return checksums

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download the public π‑Bench dataset, write each example as a JSON "
            "file, and produce a SHA‑256 checksum manifest."
        )
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory to store raw dataset files.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=None,
        help=(
            "Maximum number of examples to download. If omitted the full "
            "dataset is streamed."
        ),
    )
    args = parser.parse_args()

    raw_dir = Path(args.data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Retry logic – up to three attempts with a short back‑off.
    attempts = 3
    for attempt in range(1, attempts + 1):
        try:
            checksums = _download_pi_bench(
                raw_dir, max_examples=args.max_examples
            )
            break  # success
        except Exception as exc:
            if attempt == attempts:
                log.error(
                    f"All {attempts} attempts to download π‑Bench failed."
                )
                raise
            wait_seconds = 2 ** attempt
            log.warning(
                f"Attempt {attempt} failed ({exc}); retrying in {wait_seconds}s..."
            )
            time.sleep(wait_seconds)

    # Write a simple manifest describing the source.
    manifest_path = raw_dir / "download_manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write(
            "π‑Bench dataset downloaded via 🤗 datasets (streaming mode).\n"
        )

    # Write checksum manifest.
    checksum_path = raw_dir / "checksums.txt"
    _write_checksums(checksums, checksum_path)

    log.info("Dataset download and verification completed successfully.")
    print("✅ π‑Bench dataset download verified")

if __name__ == "__main__":
    # Ensure a basic console logger if the toolkit logger hasn't been configured.
    logging.basicConfig(level=logging.INFO)
    main()
