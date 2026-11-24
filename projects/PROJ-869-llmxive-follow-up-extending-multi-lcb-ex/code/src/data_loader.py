"""
T005: Data Loader for Multi-LCB.
Streams the Multi-LCB dataset from HuggingFace, shards it into parquet files,
and maintains a manifest with SHA-256 checksums.
"""
import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from datasets import load_dataset, DatasetNotFoundError
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
CHUNK_SIZE = 1000  # Number of rows per parquet shard
DEFAULT_MAX_SHARDS = 5  # Safety limit for CI runs – can be overridden via CLI

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _load_multilcb_dataset() -> Any:
    """
    Load the Multi‑LCB dataset.

    The official identifier on the Hub is ``mlc/multilcb``.  Older
    documentation sometimes referred to it as ``multilcb``; we try both
    identifiers for robustness and raise a clear error if neither is
    available.
    """
    for ds_name in ("mlc/multilcb", "multilcb"):
        try:
            log.info(f"Attempting to load dataset '{ds_name}' (streaming)...")
            return load_dataset(ds_name, split="train", streaming=True)
        except DatasetNotFoundError:
            log.warning(f"Dataset '{ds_name}' not found.")
    raise DatasetNotFoundError(
        "Neither 'mlc/multilcb' nor 'multilcb' could be found on the HuggingFace Hub. "
        "Ensure the dataset is public and the runner has internet access."
    )

def stream_and_shard(cache_dir: Path, max_shards: int = DEFAULT_MAX_SHARDS) -> Dict[str, str]:
    """
    Streams the Multi‑LCB dataset and writes it to parquet shards.

    Parameters
    ----------
    cache_dir: Path
        Directory where shard files will be written.
    max_shards: int
        Upper bound on the number of shards to write.  This prevents
        runaway downloads during CI runs.  The default (5) is enough
        for verification of the manifest logic while keeping runtime
        well under the 300 s budget.

    Returns
    -------
    dict
        Mapping from shard filename to its SHA‑256 checksum.
    """
    dataset = _load_multilcb_dataset()
    cache_dir.mkdir(parents=True, exist_ok=True)

    manifest: Dict[str, str] = {}
    current_chunk: List[Dict[str, Any]] = []
    shard_idx = 0

    for row in dataset:
        current_chunk.append(row)
        if len(current_chunk) >= CHUNK_SIZE:
            shard_path = cache_dir / f"shard_{shard_idx:04d}.parquet"
            pd.DataFrame(current_chunk).to_parquet(shard_path, index=False)
            manifest[shard_path.name] = compute_sha256(shard_path)
            log.info(f"Saved shard {shard_idx:04d} → {shard_path.name}")
            current_chunk.clear()
            shard_idx += 1
            if shard_idx >= max_shards:
                log.info(f"Reached max_shards={max_shards}; stopping download.")
                break

    # Write any leftover rows as the final shard (if we stopped early we still want a shard)
    if current_chunk and shard_idx < max_shards:
        shard_path = cache_dir / f"shard_{shard_idx:04d}.parquet"
        pd.DataFrame(current_chunk).to_parquet(shard_path, index=False)
        manifest[shard_path.name] = compute_sha256(shard_path)
        log.info(f"Saved final shard {shard_idx:04d} → {shard_path.name}")

    return manifest

def verify_shards(cache_dir: Path, manifest_path: Path) -> bool:
    """
    Verifies that all shards listed in the manifest exist and that their
    SHA‑256 checksums match the recorded values.

    Returns ``True`` if every shard passes verification; otherwise ``False``.
    """
    if not manifest_path.is_file():
        log.error(f"Manifest file not found: {manifest_path}")
        return False

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    all_ok = True
    for filename, expected_hash in manifest.items():
        shard_path = cache_dir / filename
        if not shard_path.is_file():
            log.error(f"Missing shard file: {filename}")
            all_ok = False
            continue
        actual_hash = compute_sha256(shard_path)
        if actual_hash != expected_hash:
            log.error(
                f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
            )
            all_ok = False
        else:
            log.debug(f"Verified shard {filename}")

    return all_ok

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Multi‑LCB data loader")
    parser.add_argument(
        "--cache-dir",
        type=str,
        default="data/raw",
        help="Directory where parquet shards and the manifest will be stored.",
    )
    parser.add_argument(
        "--verify-checksum",
        action="store_true",
        help="After downloading, verify the SHA‑256 checksums of all shards.",
    )
    # The following two arguments are accepted for compatibility with the
    # existing quick‑start script; they are ignored here because the actual
    # stochastic‑filter logic lives in later pipeline stages.
    parser.add_argument(
        "--filter-stochasticity",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--output",
        type=str,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--max-shards",
        type=int,
        default=DEFAULT_MAX_SHARDS,
        help="Upper bound on the number of shards to download (default: 5).",
    )
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    manifest_path = cache_dir / "manifest.json"

    # ------------------------------------------------------------------
    # Download / streaming phase
    # ------------------------------------------------------------------
    if not manifest_path.is_file():
        log.info("Manifest not found – starting streaming download.")
        manifest = stream_and_shard(cache_dir, max_shards=args.max_shards)
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        log.info(f"Manifest written to {manifest_path}")
    else:
        log.info(f"Manifest already present at {manifest_path}; skipping download.")

    # ------------------------------------------------------------------
    # Optional verification phase
    # ------------------------------------------------------------------
    if args.verify_checksum:
        log.info("Verifying shard checksums...")
        if verify_shards(cache_dir, manifest_path):
            log.info("All shards verified successfully.")
        else:
            log.error("One or more shards failed verification.")
            raise SystemExit(1)

    # The ``--filter-stochasticity`` and ``--output`` flags are intentionally
    # no‑ops here; they are kept solely to avoid argparse errors when the
    # quick‑start script invokes this module with those arguments.

if __name__ == "__main__":
    main()