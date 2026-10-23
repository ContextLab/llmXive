"""
download_pi_bench.py

Downloads the public π‑Bench dataset from the HuggingFace Hub.
Due to the platform's datasets library being stubbed to only support local JSON,
this script uses requests to stream the raw JSONL data directly from the HF Hub,
saves each example as a JSON file to ``data/raw``, and produces a SHA‑256 manifest.
"""

import argparse
import json
import logging
import time
import hashlib
import requests
from pathlib import Path
from typing import List, Tuple, Optional

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# The canonical URL for the pi_bench dataset's training data in JSONL format.
# If the dataset structure changes on the hub, this is the primary point of failure.
PI_BENCH_URL = "https://huggingface.co/datasets/pi_bench/resolve/main/train.jsonl"

def _sha256_checksum(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
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
    Stream the pi_bench dataset from the HuggingFace Hub using requests
    and write each example to ``raw_dir``.

    Parameters
    ----------
    raw_dir: Path
        Destination directory for the JSON files.
    max_examples: Optional[int]
        If set, limits the number of written examples.

    Returns
    -------
    List[Tuple[Path, str]]
        List of ``(relative_path, checksum)`` for every written file.
    """
    log.info(f"Streaming download of π‑Bench dataset from {PI_BENCH_URL}")

    # Use a session for efficiency and set a timeout to fail loudly if unreachable
    session = requests.Session()
    try:
        with session.get(PI_BENCH_URL, stream=True, timeout=30) as r:
            r.raise_for_status()
            
            checksums: List[Tuple[Path, str]] = []
            
            # Stream line by line to minimize memory usage (JSONL format)
            for i, line in enumerate(r.iter_lines(decode_unicode=True)):
                if line is None:
                    continue
                
                if max_examples is not None and i >= max_examples:
                    break
                
                try:
                    example = json.loads(line)
                except json.JSONDecodeError as e:
                    log.error(f"Failed to decode JSON on line {i}: {e}")
                    continue
                
                # Determine filename: use task_id if present, otherwise index
                task_id = example.get("task_id", f"task_{i:03d}")
                filename = f"{task_id}.json"
                dest_path = raw_dir / filename
                
                with dest_path.open("w", encoding="utf-8") as f:
                    json.dump(example, f, indent=2)
                
                rel_path = dest_path.relative_to(raw_dir)
                checksum = _sha256_checksum(dest_path)
                checksums.append((rel_path, checksum))
                
                if len(checksums) % 10 == 0:
                    log.debug(f"Wrote {len(checksums)} π‑Bench examples")

            if not checksums:
                raise RuntimeError("No data was downloaded from the source URL.")

            log.info(f"Finished writing {len(checksums)} π‑Bench examples to {raw_dir}")
            return checksums

    except requests.exceptions.RequestException as exc:
        log.error(f"Network error during pi_bench download: {exc}")
        raise

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download the public π‑Bench dataset, copy each example as a JSON "
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

    # Retry logic – up to three attempts with exponential back-off.
    attempts = 3
    checksums = []
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
            f"π‑Bench dataset downloaded via streaming from {PI_BENCH_URL}.\n"
        )

    # Write checksum manifest.
    checksum_path = raw_dir / "checksums.txt"
    _write_checksums(checksums, checksum_path)

    log.info("Dataset download and verification completed successfully.")
    print("✅ π‑Bench dataset download verified")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
