"""
Sample exactly 800 Python functions from the HuggingFace `codeparrot/github-code` dataset
using streaming mode, and write them to `data/raw/sample_functions.jsonl`.

The script logs the number of sampled functions and aborts with an explicit error
if fewer than 800 functions are obtained.
"""

import json
import logging
import numpy as np
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

# Configure logger
log = get_logger(__name__)

def sample_functions(
    dataset_id: str = "codeparrot/github-code",
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
    log.info(f"Streaming dataset {dataset_id} (split={split})")
    ds = load_dataset(dataset_id, split=split, streaming=True)

    candidates = []
    for item in ds:
        code = item.get("code")
        if code and isinstance(code, str) and code.strip():
            candidates.append(
                {
                    "code": code,
                    "repo": item.get("repo", "unknown"),
                    "language": item.get("language", "unknown"),
                }
            )
            if len(candidates) >= candidate_pool:
                break

    if len(candidates) < target_count:
        raise RuntimeError(
            f"Insufficient candidate functions: required {target_count}, "
            f"found {len(candidates)}"
        )

    rng = np.random.default_rng(seed)
    selected_indices = rng.choice(len(candidates), size=target_count, replace=False)
    selected = [candidates[i] for i in selected_indices]

    return selected

def main() -> None:
    """Entry point: perform sampling and write results to JSONL."""
    sampled = sample_functions()
    sampled_count = len(sampled)
    log.info(f"Sampled {sampled_count} functions")

    if sampled_count < 800:
        raise RuntimeError(
            f"Sampled count {sampled_count} is less than the required 800 functions"
        )

    output_path = paths.data("raw", "sample_functions.jsonl")
    log.info(f"Writing sampled functions to {output_path}")

    with output_path.open("w", encoding="utf-8") as f:
        for entry in sampled:
            json.dump(entry, f)
            f.write("\n")

    log.info("Sampling completed successfully")

if __name__ == "__main__":
    main()