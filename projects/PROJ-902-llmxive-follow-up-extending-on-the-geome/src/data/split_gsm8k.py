"""
GSM8K Dataset Splitting Logic.

This module implements the stratified splitting of the GSM8K dataset into
training, evaluation, and a held-out generalization subset.

It satisfies User Story 1 (US1) and User Story 2 (US2) requirements for
data partitioning.

Splits are stratified by estimated difficulty to ensure balanced
representation across the dataset.
"""

from __future__ import annotations

import json
import hashlib
import random
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from datasets import load_dataset


# Default split ratios based on project consensus (derived from T009b-deferred)
# 70% Train, 15% Eval, 15% Held-out Generalization
DEFAULT_TRAIN_RATIO = 0.70
DEFAULT_EVAL_RATIO = 0.15
DEFAULT_HOLDOUT_RATIO = 0.15


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def estimate_difficulty(example: Dict[str, Any]) -> int:
    """
    Estimate difficulty of a GSM8K problem based on solution length.

    This is a heuristic proxy for difficulty:
    - Short solutions (< 200 chars): Easy
    - Medium solutions (200-500 chars): Medium
    - Long solutions (> 500 chars): Hard

    Args:
        example: A dictionary containing 'question' and 'answer' keys.

    Returns:
        An integer representing the difficulty bucket (0: Easy, 1: Medium, 2: Hard).
    """
    solution_text = example.get("answer", "")
    # GSM8K answers usually end with "####" followed by the number.
    # We count the length of the reasoning part.
    if "####" in solution_text:
        reasoning = solution_text.split("####")[0]
    else:
        reasoning = solution_text

    length = len(reasoning)

    if length < 200:
        return 0  # Easy
    elif length < 500:
        return 1  # Medium
    else:
        return 2  # Hard


def stratified_split(
    dataset: Any,
    train_ratio: float = DEFAULT_TRAIN_RATIO,
    eval_ratio: float = DEFAULT_EVAL_RATIO,
    holdout_ratio: float = DEFAULT_HOLDOUT_RATIO,
    seed: int = 42
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Perform a stratified split of the dataset into train, eval, and holdout sets.

    Stratification is performed based on the estimated difficulty of each example.

    Args:
        dataset: The loaded HuggingFace dataset object.
        train_ratio: Fraction of data for training.
        eval_ratio: Fraction of data for evaluation.
        holdout_ratio: Fraction of data for held-out generalization.
        seed: Random seed for reproducibility.

    Returns:
        A tuple of (train_list, eval_list, holdout_list).
    """
    if not (abs(train_ratio + eval_ratio + holdout_ratio - 1.0) < 1e-6):
        raise ValueError(
            f"Ratios must sum to 1.0. Got: {train_ratio + eval_ratio + holdout_ratio}"
        )

    random.seed(seed)

    # Convert dataset to list for easier manipulation if it's not already
    # HuggingFace datasets can be iterated or converted to list
    if hasattr(dataset, "to_list"):
        data_list = dataset.to_list()
    else:
        data_list = list(dataset)

    # Annotate each example with difficulty
    annotated_data = []
    for item in data_list:
        difficulty = estimate_difficulty(item)
        annotated_data.append({"data": item, "difficulty": difficulty})

    # Group by difficulty
    difficulty_groups: Dict[int, List[Dict]] = {0: [], 1: [], 2: []}
    for entry in annotated_data:
        difficulty_groups[entry["difficulty"]].append(entry)

    train_data: List[Dict] = []
    eval_data: List[Dict] = []
    holdout_data: List[Dict] = []

    # Split each group
    for diff_level, group in difficulty_groups.items():
        random.shuffle(group)
        n = len(group)

        n_train = int(n * train_ratio)
        n_eval = int(n * eval_ratio)
        # Remaining go to holdout to ensure exact sum
        n_holdout = n - n_train - n_eval

        train_data.extend([entry["data"] for entry in group[:n_train]])
        eval_data.extend([entry["data"] for entry in group[n_train : n_train + n_eval]])
        holdout_data.extend([entry["data"] for entry in group[n_train + n_eval :]])

    return train_data, eval_data, holdout_data


def save_splits(
    train_data: List[Dict],
    eval_data: List[Dict],
    holdout_data: List[Dict],
    output_dir: Path,
    seed: int = 42
) -> Dict[str, str]:
    """
    Save the split datasets to JSON files and record checksums.

    Args:
        train_data: List of training examples.
        eval_data: List of evaluation examples.
        holdout_data: List of held-out examples.
        output_dir: Directory to save the files.
        seed: The seed used for splitting (for metadata).

    Returns:
        A dictionary mapping file names to their SHA-256 checksums.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    files_to_save = [
        ("gsm8k_train.json", train_data),
        ("gsm8k_eval.json", eval_data),
        ("gsm8k_holdout.json", holdout_data),
    ]

    checksums = {}

    for filename, data in files_to_save:
        file_path = output_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        checksums[filename] = compute_sha256(file_path)

    # Save metadata
    metadata = {
        "seed": seed,
        "ratios": {
            "train": DEFAULT_TRAIN_RATIO,
            "eval": DEFAULT_EVAL_RATIO,
            "holdout": DEFAULT_HOLDOUT_RATIO
        },
        "checksums": checksums,
        "counts": {
            "train": len(train_data),
            "eval": len(eval_data),
            "holdout": len(holdout_data)
        }
    }

    meta_path = output_dir / "split_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return checksums


def main():
    """
    Main entry point to download (if needed) and split the GSM8K dataset.

    This script assumes the dataset is available via the HuggingFace `datasets`
    library under the 'gsm8k' config 'main'. It will attempt to load it.
    If the raw files exist in data/raw, it could load from there, but for
    simplicity and standard practice, we use the HF loader which handles
    caching.
    """
    output_dir = Path("data/splits")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading GSM8K dataset...")
    try:
        # Load the main GSM8K dataset
        # The 'main' config is the standard one
        dataset = load_dataset("gsm8k", "main", split="train")
    except Exception as e:
        print(f"Error loading dataset: {e}")
        # Fail loudly as per constraints
        raise RuntimeError("Failed to load GSM8K dataset from HuggingFace. "
                         "Ensure internet connection and 'datasets' package installed.") from e

    print(f"Loaded {len(dataset)} examples.")

    print("Performing stratified split...")
    train, eval, holdout = stratified_split(
        dataset,
        seed=42,
        train_ratio=DEFAULT_TRAIN_RATIO,
        eval_ratio=DEFAULT_EVAL_RATIO,
        holdout_ratio=DEFAULT_HOLDOUT_RATIO
    )

    print(f"Split complete: Train={len(train)}, Eval={len(eval)}, Holdout={len(holdout)}")

    print(f"Saving splits to {output_dir}...")
    checksums = save_splits(train, eval, holdout, output_dir, seed=42)

    print("Split files saved successfully.")
    print("Checksums:")
    for fname, cs in checksums.items():
        print(f"  {fname}: {cs}")

    # Verify metadata
    meta_path = output_dir / "split_metadata.json"
    if meta_path.exists():
        print(f"Metadata saved to {meta_path}")
    else:
        raise RuntimeError("Failed to save metadata file.")


if __name__ == "__main__":
    main()