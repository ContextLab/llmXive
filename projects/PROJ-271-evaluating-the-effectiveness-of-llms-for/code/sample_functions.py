"""
Sample exactly 800 Python functions from the HuggingFace `codeparrot/github-code`
dataset using streaming mode, and write them to `data/raw/sample_functions.jsonl`.

The script logs the number of sampled functions and aborts with an explicit error
if fewer than 800 functions are obtained.

It first attempts to stream the dataset directly. If the dataset provides
Parquet shards (as on the `refs/convert/parquet` branch), those are used for
efficiency; otherwise, it falls back to the standard streaming interface.
"""

import json
import logging
from pathlib import Path

import numpy as np
from datasets import load_dataset
from huggingface_hub import HfFileSystem

from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

DATASET_ID = "codeparrot/github-code"
PARQUET_REVISION = "refs/convert/parquet"


def _list_parquet_shards(max_files: int = 2) -> list[Path]:
    """
    List Parquet shard files for the Python subset on the parquet branch.

    Returns a list of Path objects (as strings) limited to ``max_files``.
    If no shards are found, returns an empty list.
    """
    fs = HfFileSystem()
    pattern = f"datasets/{DATASET_ID}@{PARQUET_REVISION}/python/train-*.parquet"
    files = sorted(fs.glob(pattern))
    if not files:
        log.debug(
            "No Parquet shards found for %s at revision %s (pattern: %s)",
            DATASET_ID,
            PARQUET_REVISION,
            pattern,
        )
        return []
    log.info("Found %d Parquet shards; using first %d", len(files), max_files)
    return files[:max_files]


def _extract_item(item: dict) -> dict | None:
    """
    Normalise a raw dataset row, returning ``None`` if the row does not
    contain usable Python source code.
    """
    # The dataset historically used either ``content`` or ``code``.
    code = item.get("content") or item.get("code")
    if not code or not isinstance(code, str) or not code.strip():
        return None

    return {
        "code": code,
        "repo": item.get("repo_name") or item.get("repo") or "unknown",
        "path": item.get("path", "unknown"),
        "language": item.get("language", "python"),
    }


def _stream_dataset(
    split: str = "train",
) -> list[dict]:
    """
    Stream the dataset (either via Parquet shards or the generic streaming
    interface) and return a list of candidate function dictionaries.
    """
    # Try the Parquet shards first – they are much faster to stream.
    parquet_files = _list_parquet_shards()
    if parquet_files:
        data_files = {split: [f"hf://{f}" for f in parquet_files]}
        log.info(
            "Streaming Parquet shards of %s (split=%s)", DATASET_ID, split
        )
        ds = load_dataset(
            "parquet", data_files=data_files, split=split, streaming=True
        )
    else:
        # Fallback to the regular streaming loader.
        log.info(
            "Falling back to regular streaming load for %s (split=%s)",
            DATASET_ID,
            split,
        )
        ds = load_dataset(DATASET_ID, split=split, streaming=True)

    candidates = []
    for item in ds:
        entry = _extract_item(item)
        if entry is not None:
            candidates.append(entry)
    return candidates


def sample_functions(
    dataset_id: str = DATASET_ID,
    split: str = "train",
    seed: int = 42,
    target_count: int = 800,
    candidate_pool: int = 5000,
) -> list[dict]:
    """
    Stream the dataset, collect a pool of candidate functions, then randomly
    select exactly ``target_count`` items using the provided ``seed`` for
    reproducibility.

    Args:
        dataset_id: HuggingFace dataset identifier (must match the constant).
        split: Dataset split to use.
        seed: Random seed for deterministic sampling.
        target_count: Number of functions to sample.
        candidate_pool: Upper bound on how many candidates to collect before
            sampling. This limits the amount of streaming work while still
            providing a reasonably diverse pool.

    Returns:
        A list of dictionaries, each containing at least the source code
        under the key ``code`` and optional metadata.
    """
    if dataset_id != DATASET_ID:
        raise ValueError(
            f"This sampler is wired to {DATASET_ID}; got {dataset_id}"
        )

    # Stream and collect candidates.
    all_candidates = _stream_dataset(split=split)

    if not all_candidates:
        raise RuntimeError(
            f"No candidate functions could be extracted from {dataset_id}"
        )

    # Limit the pool size to ``candidate_pool`` for efficiency.
    if len(all_candidates) > candidate_pool:
        all_candidates = all_candidates[:candidate_pool]

    log.info("Collected %d candidate functions", len(all_candidates))

    if len(all_candidates) < target_count:
        raise RuntimeError(
            f"Insufficient candidate functions: required {target_count}, "
            f"found {len(all_candidates)}"
        )

    rng = np.random.default_rng(seed)
    selected_indices = rng.choice(
        len(all_candidates), size=target_count, replace=False
    )
    selected = [all_candidates[i] for i in selected_indices]

    return selected


def main() -> None:
    """Entry point: perform sampling and write results to JSONL."""
    sampled = sample_functions()
    sampled_count = len(sampled)
    log.info("Sampled %d functions", sampled_count)

    if sampled_count < 800:
        raise RuntimeError(
            f"Sampled count {sampled_count} is less than the required 800 functions"
        )

    output_path = paths.data("raw", "sample_functions.jsonl")
    log.info("Writing sampled functions to %s", output_path)

    # Ensure the parent directory exists (paths.data creates it).
    with output_path.open("w", encoding="utf-8") as f:
        for entry in sampled:
            json.dump(entry, f)
            f.write("\n")

    log.info("Sampling completed successfully")


if __name__ == "__main__":
    # Configure a basic logger if the toolkit logger is not set up yet.
    logging.basicConfig(level=logging.INFO)
    main()