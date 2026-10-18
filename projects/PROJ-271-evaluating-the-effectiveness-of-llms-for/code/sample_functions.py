"""
Sample exactly 800 Python functions from the HuggingFace `codeparrot/github-code`
dataset using streaming mode, and write them to `data/raw/sample_functions.jsonl`.

The script logs the number of sampled functions and aborts with an explicit error
if fewer than 800 functions are obtained.
"""

import json
import logging
import numpy as np
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

DATASET_ID = "codeparrot/github-code"

def sample_functions(
    dataset_id: str = DATASET_ID,
    split: str = "train",
    seed: int = 42,
    target_count: int = 800,
    candidate_pool_limit: int = 5000,
) -> list[dict]:
    """
    Stream the dataset and collect a pool of candidate functions, then randomly
    select exactly ``target_count`` items using the provided ``seed`` for
    reproducibility.

    Args:
        dataset_id: HuggingFace dataset identifier.
        split: Dataset split to use.
        seed: Random seed for deterministic sampling.
        target_count: Number of functions to sample.
        candidate_pool_limit: Upper bound on how many candidates to collect 
            before sampling to avoid OOM or excessive streaming.

    Returns:
        A list of dictionaries, each containing at least the source code.
    """
    log.info("Streaming dataset %s (split=%s)...", dataset_id, split)
    
    # Use streaming=True as required by T007
    ds = load_dataset(dataset_id, split=split, streaming=True)

    candidates = []
    for item in ds:
        # Extract code from either 'content' or 'code' field
        code = item.get("content") or item.get("code")
        if code and isinstance(code, str) and code.strip():
            candidates.append({
                "code": code,
                "repo": item.get("repo_name") or item.get("repo") or "unknown",
                "path": item.get("path", "unknown"),
                "language": item.get("language", "python"),
            })
        
        # CRITICAL: Break early to avoid streaming the entire dataset into memory
        if len(candidates) >= candidate_pool_limit:
            break

    log.info("Collected %d candidate functions", len(candidates))

    if len(candidates) < target_count:
        raise RuntimeError(
            f"Insufficient candidate functions: required {target_count}, "
            f"found {len(candidates)}"
        )

    # Deterministic sampling from the collected pool
    rng = np.random.default_rng(seed)
    selected_indices = rng.choice(
        len(candidates), size=target_count, replace=False
    )
    selected = [candidates[i] for i in selected_indices]

    return selected

def main() -> None:
    """Entry point: perform sampling and write results to JSONL."""
    try:
        sampled = sample_functions()
        sampled_count = len(sampled)
        log.info("Sampled %d functions", sampled_count)

        if sampled_count < 800:
            # This is a safety check; sample_functions should already raise RuntimeError
            raise RuntimeError(
                f"Sampled count {sampled_count} is less than the required 800 functions"
            )

        # Path provided by toolkit ensures directory existence
        output_path = paths.data("raw", "sample_functions.jsonl")
        log.info("Writing sampled functions to %s", output_path)

        with output_path.open("w", encoding="utf-8") as f:
            for entry in sampled:
                f.write(json.dumps(entry) + "\n")

        log.info("Sampling completed successfully")
    except Exception as e:
        log.error("Sampling failed: %s", e)
        raise

if __name__ == "__main__":
    # Setup basic logging in case toolkit logger isn't fully initialized
    logging.basicConfig(level=logging.INFO)
    main()