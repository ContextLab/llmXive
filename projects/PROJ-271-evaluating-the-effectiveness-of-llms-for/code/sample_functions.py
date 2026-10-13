"""
Sample exactly 800 Python functions from the HuggingFace `codeparrot/github-code`
dataset using streaming mode, and write them to `data/raw/sample_functions.jsonl`.

The script logs the number of sampled functions and aborts with an explicit error
if fewer than 800 functions are obtained.

Note on data access: the `codeparrot/github-code` repository on `main` is a
script-based dataset, which recent versions of the `datasets` library refuse to
load ("Dataset scripts are no longer supported"). The same data is available as
auto-converted Parquet files on the `refs/convert/parquet` branch of the same
repository; we stream those files directly, which keeps the data source real
(same dataset, same content) while remaining compatible with modern `datasets`.
"""

import json

import numpy as np
from datasets import load_dataset
from huggingface_hub import HfFileSystem

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

DATASET_ID = "codeparrot/github-code"
PARQUET_REVISION = "refs/convert/parquet"


def _python_parquet_files(max_files: int = 2) -> list:
    """List real Parquet shards of the Python config on the parquet branch."""
    fs = HfFileSystem()
    pattern = (
        f"datasets/{DATASET_ID}@{PARQUET_REVISION}/python/train-*.parquet"
    )
    files = sorted(fs.glob(pattern))
    if not files:
        raise RuntimeError(
              f"No Parquet files found for {DATASET_ID} at "
              f"{PARQUET_REVISION} (pattern: {pattern})"
        )
    log.info(
        "Found %d Parquet shards; using first %d", len(files), max_files
    )
    return files[:max_files]


def _extract(item: dict) -> dict | None:
    """Normalize a raw dataset row, returning None if unusable."""
    code = item.get("content") or item.get("code")
    if not code or not isinstance(code, str) or not code.strip():
        return None
    return {
        "code": code,
        "repo": item.get("repo_name") or item.get("repo") or "unknown",
        "path": item.get("path", "unknown"),
        "language": item.get("language", "python"),
    }


def sample_functions(
    dataset_id: str = DATASET_ID,
    split: str = "train",
    seed: int = 42,
    target_count: int = 800,
    candidate_pool: int = 5000,
) -> list:
    """
    Stream the dataset, collect a pool of candidate functions, then randomly
    select exactly ``target_count`` items using the provided ``seed`` for
    reproducibility.

    Args:
        dataset_id: HuggingFace dataset identifier.
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

    files = _python_parquet_files()
    data_files = {split: [f"hf://{f}" for f in files]}
    log.info(
        "Streaming Parquet shards of %s (split=%s)", dataset_id, split
    )
    ds = load_dataset(
        "parquet", data_files=data_files, split=split, streaming=True
    )

    candidates = []
    for item in ds:
        entry = _extract(item)
        if entry is not None:
            candidates.append(entry)
            if len(candidates) >= candidate_pool:
                break

    log.info("Collected %d candidate functions", len(candidates))

    if len(candidates) < target_count:
        raise RuntimeError(
            f"Insufficient candidate functions: required {target_count}, "
            f"found {len(candidates)}"
        )

    rng = np.random.default_rng(seed)
    selected_indices = rng.choice(
        len(candidates), size=target_count, replace=False
    )
    selected = [candidates[i] for i in selected_indices]

    return selected


def main() -> None:
    """Entry point: perform sampling and write results to JSONL."""
    sampled = sample_functions()
    sampled_count = len(sampled)
    log.info("Sampled %d functions", sampled_count)

    if sampled_count < 800:
        raise RuntimeError(
            f"Sampled count {sampled_count} is less than the required "
            "800 functions"
        )

    output_path = paths.data("raw", "sample_functions.jsonl")
    log.info("Writing sampled functions to %s", output_path)

    with output_path.open("w", encoding="utf-8") as f:
        for entry in sampled:
            json.dump(entry, f)
            f.write("\n")

    log.info("Sampling completed successfully")


if __name__ == "__main__":
    main()
