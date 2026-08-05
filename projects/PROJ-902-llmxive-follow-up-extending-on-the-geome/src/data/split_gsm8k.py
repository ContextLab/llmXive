"""
GSM8K Data Splitting Module

Splits the GSM8K dataset into training, evaluation, and held-out generalization subsets.
Stratifies splits by difficulty to ensure balanced representation across all sets.
Persists splits to data/gsm8k/splits/ in Parquet format.
"""
import hashlib
import json
import os
import random
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
from datasets import load_dataset

# Constants for split ratios
TRAIN_RATIO = 0.8
EVAL_RATIO = 0.1
GENERALIZATION_RATIO = 0.1

# Output directory
SPLIT_DIR = Path("data/gsm8k/splits")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def estimate_difficulty(example: Dict[str, Any]) -> int:
    """
    Estimate difficulty based on the number of reasoning steps.
    Heuristic: Count the number of lines in the solution that contain arithmetic operations.
    Returns an integer difficulty score (0-5).
    """
    solution = example.get("answer", "")
    # Extract the reasoning part (everything before "####")
    if "####" in solution:
        reasoning = solution.split("####")[0]
    else:
        reasoning = solution

    # Count lines with arithmetic operations
    lines = reasoning.strip().split("\n")
    difficulty_score = 0
    for line in lines:
        # Check for common arithmetic patterns
        if any(op in line for op in ["+", "-", "*", "/", "="]):
            difficulty_score += 1

    # Normalize to 0-5 range based on typical GSM8K lengths
    # GSM8K solutions are typically 10-30 lines
    if difficulty_score <= 5:
        return 0
    elif difficulty_score <= 10:
        return 1
    elif difficulty_score <= 15:
        return 2
    elif difficulty_score <= 20:
        return 3
    elif difficulty_score <= 25:
        return 4
    else:
        return 5


def stratified_split(
    dataset: List[Dict[str, Any]],
    train_ratio: float = TRAIN_RATIO,
    eval_ratio: float = EVAL_RATIO,
    gen_ratio: float = GENERALIZATION_RATIO,
    seed: int = 42
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Split dataset into train, eval, and generalization sets with stratification by difficulty.

    Args:
        dataset: List of GSM8K examples.
        train_ratio: Proportion for training.
        eval_ratio: Proportion for evaluation.
        gen_ratio: Proportion for held-out generalization.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_set, eval_set, generalization_set)
    """
    random.seed(seed)
    np.random.seed(seed)

    # Group examples by difficulty
    difficulty_buckets: Dict[int, List[Dict]] = defaultdict(list)
    for example in dataset:
        diff = estimate_difficulty(example)
        difficulty_buckets[diff].append(example)

    train_set = []
    eval_set = []
    generalization_set = []

    # Stratified split within each difficulty bucket
    for diff_level, examples in difficulty_buckets.items():
        random.shuffle(examples)
        n = len(examples)

        n_train = int(n * train_ratio)
        n_eval = int(n * eval_ratio)
        # Remaining go to generalization
        n_gen = n - n_train - n_eval

        train_set.extend(examples[:n_train])
        eval_set.extend(examples[n_train : n_train + n_eval])
        generalization_set.extend(examples[n_train + n_eval :])

    # Shuffle final sets for better distribution
    random.shuffle(train_set)
    random.shuffle(eval_set)
    random.shuffle(generalization_set)

    return train_set, eval_set, generalization_set


def save_splits(
    train_set: List[Dict],
    eval_set: List[Dict],
    generalization_set: List[Dict],
    output_dir: Path,
    seed: int = 42
) -> Dict[str, str]:
    """
    Save splits to Parquet files and compute checksums.

    Returns:
        Dictionary mapping split name to file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    splits = {
        "train": train_set,
        "eval": eval_set,
        "generalization": generalization_set,
    }

    file_paths = {}
    checksums = {}

    for split_name, data in splits.items():
        file_path = output_dir / f"gsm8k_{split_name}_seed{seed}.parquet"
        # Convert to dataset for Parquet export
        from datasets import Dataset
        ds = Dataset.from_list(data)
        ds.to_parquet(str(file_path))

        file_paths[split_name] = str(file_path)
        checksums[split_name] = compute_sha256(file_path)

    # Save checksums JSON
    checksum_file = output_dir / f"splits_checksums_seed{seed}.json"
    with open(checksum_file, "w") as f:
        json.dump(checksums, f, indent=2)

    return file_paths


def load_gsm8k_streaming() -> List[Dict[str, Any]]:
    """
    Load GSM8K dataset using streaming mode.
    Returns a list of examples.
    """
    # Load the 'main' split of gsm8k
    ds = load_dataset("gsm8k", "main", split="train", streaming=True)

    examples = []
    for item in ds:
        examples.append(item)

    return examples


def main(seed: int = 42) -> Dict[str, Any]:
    """
    Main entry point for splitting GSM8K.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        Dictionary containing split statistics and file paths.
    """
    print(f"Starting GSM8K split with seed={seed}")

    # Load dataset
    print("Loading GSM8K dataset (streaming)...")
    examples = load_gsm8k_streaming()
    print(f"Loaded {len(examples)} examples")

    # Perform stratified split
    print("Performing stratified split by difficulty...")
    train_set, eval_set, generalization_set = stratified_split(
        examples, seed=seed
    )

    print(f"Train size: {len(train_set)}")
    print(f"Eval size: {len(eval_set)}")
    print(f"Generalization size: {len(generalization_set)}")

    # Save splits
    print(f"Saving splits to {SPLIT_DIR}...")
    file_paths = save_splits(train_set, eval_set, generalization_set, SPLIT_DIR, seed)

    # Compute statistics
    stats = {
        "seed": seed,
        "total_examples": len(examples),
        "train_count": len(train_set),
        "eval_count": len(eval_set),
        "generalization_count": len(generalization_set),
        "file_paths": file_paths,
        "split_ratios": {
            "train": len(train_set) / len(examples),
            "eval": len(eval_set) / len(examples),
            "generalization": len(generalization_set) / len(examples),
        }
    }

    # Save stats JSON
    stats_file = SPLIT_DIR / f"splits_stats_seed{seed}.json"
    with open(stats_file, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Split complete. Stats saved to {stats_file}")
    return stats


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split GSM8K dataset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    main(seed=args.seed)
