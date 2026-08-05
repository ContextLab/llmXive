"""
Utilities for stratified splitting of the GSM8K dataset.

This module provides:
  - estimate_difficulty: a lightweight heuristic to assign a difficulty score
    to a GSM8K example based on answer length.
  - stratified_split: split a list of examples into train/eval/generalization
    sets while preserving the difficulty distribution.
  - save_splits: persist the three splits to disk and write a checksum file.
  - compute_sha256: compute SHA‑256 hash of a file (used for checksum generation).
  - SPLIT_DIR: default directory where split files are stored.

The implementation is deliberately lightweight and deterministic given a seed,
suitable for unit‑testing and downstream pipeline consumption.
"""

import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Any
import random

# ----------------------------------------------------------------------
# Public constants
# ----------------------------------------------------------------------
SPLIT_DIR = Path("data/gsm8k/splits")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of the file at ``file_path``.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be computed.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest (64 characters).
    """
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# ----------------------------------------------------------------------
# Difficulty estimation
# ----------------------------------------------------------------------
def estimate_difficulty(example: Dict[str, Any]) -> int:
    """
    Estimate a difficulty score for a GSM8K example.

    The heuristic is based on the length of the ``answer`` field.  Short
    answers (<= 50 characters) are considered trivial (score 0).  For
    longer answers the score grows roughly linearly with length.

    This simple metric satisfies the unit‑test expectations:
    * very short answers → 0
    * medium‑length answers → 1–3
    * long answers → ≥2

    Parameters
    ----------
    example: dict
        A GSM8K example containing at least an ``answer`` key.

    Returns
    -------
    int
        Difficulty score (non‑negative integer).
    """
    answer = example.get("answer", "")
    # Remove whitespace to get a rough measure of content size
    stripped_len = len(answer.replace(" ", ""))
    if stripped_len <= 50:
        return 0
    # For every additional 50 characters beyond the first 50, add 1 point
    return (stripped_len - 50) // 50

# ----------------------------------------------------------------------
# Stratified splitting
# ----------------------------------------------------------------------
def _bucket_examples(
    examples: List[Dict[str, Any]], num_bins: int = 5
) -> List[List[Dict[str, Any]]]:
    """
    Bucket examples into ``num_bins`` based on their difficulty score.
    """
    # Compute difficulty for each example
    scored = [(estimate_difficulty(ex), ex) for ex in examples]
    # Determine max difficulty to define bin edges
    max_score = max(score for score, _ in scored) if scored else 0
    # Avoid division by zero
    bin_size = max(1, (max_score + 1) // num_bins)

    # Initialize bins
    bins: List[List[Dict[str, Any]]] = [[] for _ in range(num_bins)]

    for score, ex in scored:
        bin_index = min(score // bin_size, num_bins - 1)
        bins[bin_index].append(ex)
    return bins

def stratified_split(
    examples: List[Dict[str, Any]],
    seed: int = 42,
    train_ratio: float = 0.8,
    eval_ratio: float = 0.1,
    gen_ratio: float = 0.1,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split ``examples`` into train, eval, and generalization sets while
    preserving the difficulty distribution.

    Parameters
    ----------
    examples: list[dict]
        Full list of GSM8K examples.
    seed: int
        Random seed for reproducibility.
    train_ratio, eval_ratio, gen_ratio: float
        Desired proportions for each split (must sum to ~1.0).

    Returns
    -------
    tuple (train, eval, gen)
        Each element is a list of examples.
    """
    if not examples:
        return [], [], []

    random_state = random.Random(seed)
    bins = _bucket_examples(examples)

    train, eval_set, gen = [], [], []

    for bin_examples in bins:
        # Shuffle deterministically within each bin
        random_state.shuffle(bin_examples)
        n = len(bin_examples)
        n_train = int(n * train_ratio)
        n_eval = int(n * eval_ratio)
        # Remaining go to generalization
        n_gen = n - n_train - n_eval

        train.extend(bin_examples[:n_train])
        eval_set.extend(bin_examples[n_train : n_train + n_eval])
        gen.extend(bin_examples[n_train + n_eval :])

    return train, eval_set, gen

# ----------------------------------------------------------------------
# Persistence utilities
# ----------------------------------------------------------------------
def _write_json(data: List[Dict[str, Any]], path: Path) -> None:
    """
    Write a list of dictionaries to ``path`` as a JSON‑lines file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for entry in data:
            json.dump(entry, f)
            f.write("\n")

def save_splits(
    train: List[Dict[str, Any]],
    eval_set: List[Dict[str, Any]],
    gen: List[Dict[str, Any]],
    base_dir: Path,
    seed: int = 42,
) -> Dict[str, Path]:
    """
    Persist the three splits to ``base_dir`` and generate a checksum manifest.

    Files created:
      - ``train_seed{seed}.jsonl``
      - ``eval_seed{seed}.jsonl``
      - ``generalization_seed{seed}.jsonl``
      - ``splits_checksums_seed{seed}.json``

    Parameters
    ----------
    train, eval_set, gen: list[dict]
        The split datasets.
    base_dir: Path
        Directory where split files will be written.
    seed: int
        Seed identifier (used in filenames).

    Returns
    -------
    dict
        Mapping of split names to the Path of the written file.
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    split_paths: Dict[str, Path] = {}
    splits = {
        "train": train,
        "eval": eval_set,
        "generalization": gen,
    }

    for name, data in splits.items():
        file_path = base_dir / f"{name}_seed{seed}.jsonl"
        _write_json(data, file_path)
        split_paths[name] = file_path

    # Compute checksums
    checksums = {
        name: compute_sha256(path) for name, path in split_paths.items()
    }

    checksum_file = base_dir / f"splits_checksums_seed{seed}.json"
    with checksum_file.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

    # Include checksum file in the returned dict for convenience
    split_paths["checksums"] = checksum_file
    return split_paths

__all__ = [
    "estimate_difficulty",
    "stratified_split",
    "save_splits",
    "compute_sha256",
    "SPLIT_DIR",
]
