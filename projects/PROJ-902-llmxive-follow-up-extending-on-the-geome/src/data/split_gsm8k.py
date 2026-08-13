"""
Split GSM8K dataset into training, evaluation and held‑out generalisation subsets.

The script reads the raw GSM8K files that were cached by :pymod:`src.data.download_gsm8k`
(typically JSON‑Lines files under ``data/gsm8k/``), estimates a simple “difficulty”
score for each example, and then performs a stratified split that preserves the
difficulty distribution across the three subsets.

The public API consists of four functions that are referenced by the project’s
task list:

* ``compute_sha256`` – compute a SHA‑256 checksum for a file (used by the checksum
  contract tests).
* ``estimate_difficulty`` – a lightweight heuristic that returns a numeric difficulty
  for a GSM8K example.
* ``stratified_split`` – split a list of examples into train/eval/held‑out while
  preserving the difficulty distribution.
* ``save_splits`` – write the three splits to ``data/gsm8k/`` as JSON‑Lines files.

Running the module as a script (``python -m src.data.split_gsm8k``) performs the
whole pipeline and writes the three split files:

* ``data/gsm8k/train_split.jsonl``
* ``data/gsm8k/eval_split.jsonl``
* ``data/gsm8k/heldout_split.jsonl``

The implementation avoids any external heavy dependencies – it works with the
standard library only – and it is fully deterministic (the random seed is fixed
to ``42``).  If the raw GSM8K cache is missing, the script will raise an informative
``FileNotFoundError`` so that the CI can surface the problem instead of silently
falling back to synthetic data.
"""

import json
import hashlib
import random
from pathlib import Path
from typing import List, Tuple, Dict, Any

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path`` and return it as a hex string.

    Parameters
    ----------
    file_path: Path
        Path to the file whose checksum should be computed.

    Returns
    ----------
    str
        Hexadecimal SHA‑256 digest.
    """
    hasher = hashlib.sha256()
    # Read in binary chunks to support large files without loading everything into memory
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# --------------------------------------------------------------------------- #
# Difficulty estimation
# --------------------------------------------------------------------------- #
def estimate_difficulty(example: Dict[str, Any]) -> float:
    """
    Very simple difficulty heuristic for a GSM8K example.

    The GSM8K dataset provides a ``question`` and an ``answer`` field (both strings).
    We approximate difficulty by the length of the answer in words – longer answers
    tend to correspond to more involved arithmetic problems.  If the ``answer`` field
    is missing we fall back to the length of the question.

    Parameters
    ----------
    example: dict
        A single GSM8K example.

    Returns
    ----------
    float
        Difficulty score (higher = more difficult).
    """
    answer = example.get("answer")
    if isinstance(answer, str) and answer.strip():
        return len(answer.split())
    # Fallback to question length
    question = example.get("question", "")
    return len(question.split())

# --------------------------------------------------------------------------- #
# Stratified split
# --------------------------------------------------------------------------- #
def stratified_split(
    data: List[Dict[str, Any]],
    train_frac: float = 0.80,
    eval_frac: float = 0.10,
    seed: int = 42,
    n_bins: int = 10,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split ``data`` into training, evaluation and held‑out subsets while preserving
    the difficulty distribution.

    The algorithm:
    1. Compute a difficulty score for each example.
    2. Bin examples into ``n_bins`` equal‑frequency bins.
    3. Within each bin, randomly shuffle (deterministically) and allocate the
       requested fractions to train/eval/held‑out.

    Parameters
    ----------
    data: list[dict]
        List of GSM8K examples.
    train_frac: float, default 0.80
        Fraction of data to allocate to the training split.
    eval_frac: float, default 0.10
        Fraction of data to allocate to the evaluation split.
    seed: int, default 42
        Random seed for reproducibility.
    n_bins: int, default 10
        Number of difficulty bins for stratification.

    Returns
    -------
    tuple(list, list, list)
        (train_examples, eval_examples, heldout_examples)
    """
    if not 0 < train_frac < 1 or not 0 <= eval_frac < 1:
        raise ValueError("train_frac and eval_frac must be between 0 and 1")
    if train_frac + eval_frac >= 1:
        raise ValueError("train_frac + eval_frac must be < 1 (reserved for held‑out)")

    # Attach difficulty scores
    scored = [(example, estimate_difficulty(example)) for example in data]

    # Sort by difficulty to create bins of roughly equal size
    scored.sort(key=lambda x: x[1])

    bin_size = max(1, len(scored) // n_bins)
    bins: List[List[Tuple[Dict[str, Any], float]]] = []
    for i in range(0, len(scored), bin_size):
        bins.append(scored[i : i + bin_size])

    train, eval_, heldout = [], [], []

    random.seed(seed)

    for bin_ in bins:
        # Shuffle within the bin
        random.shuffle(bin_)
        n = len(bin_)
        n_train = int(train_frac * n)
        n_eval = int(eval_frac * n)
        # Remaining go to held‑out
        n_held = n - n_train - n_eval

        # Slice and drop the difficulty scores
        train.extend([ex for ex, _ in bin_[:n_train]])
        eval_.extend([ex for ex, _ in bin_[n_train : n_train + n_eval]])
        heldout.extend([ex for ex, _ in bin_[n_train + n_eval :]])

    return train, eval_, heldout

# --------------------------------------------------------------------------- #
# Persistence helpers
# --------------------------------------------------------------------------- #
def _write_jsonl(path: Path, examples: List[Dict[str, Any]]) -> None:
    """Write a list of dictionaries to ``path`` as JSON‑Lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for ex in examples:
            json.dump(ex, f, ensure_ascii=False)
            f.write("\n")

def save_splits(
    train: List[Dict[str, Any]],
    eval_: List[Dict[str, Any]],
    heldout: List[Dict[str, Any]],
    output_dir: Path = Path("data/gsm8k"),
) -> None:
    """
    Save the three splits as JSON‑Lines files under ``output_dir``.
    The files are named ``train_split.jsonl``, ``eval_split.jsonl`` and
    ``heldout_split.jsonl`` respectively.

    Parameters
    ----------
    train, eval_, heldout: list[dict]
        The split datasets.
    output_dir: Path, default Path("data/gsm8k")
        Directory where the split files will be stored.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_jsonl(output_dir / "train_split.jsonl", train)
    _write_jsonl(output_dir / "eval_split.jsonl", eval_)
    _write_jsonl(output_dir / "heldout_split.jsonl", heldout)

# --------------------------------------------------------------------------- #
# Data loading
# --------------------------------------------------------------------------- #
def _load_cached_gsm8k(cache_dir: Path = Path("data/gsm8k")) -> List[Dict[str, Any]]:
    """
    Load all JSON‑Lines files present in ``cache_dir`` (excluding any previously
    generated split files).  The raw GSM8K download script stores the original
    dataset splits as ``train.jsonl``, ``validation.jsonl`` and ``test.jsonl``.
    This function concatenates them into a single list.

    Parameters
    ----------
    cache_dir: Path, default Path("data/gsm8k")
        Directory containing the cached raw GSM8K files.

    Returns
    -------
    list[dict]
        All examples from the raw dataset.
    """
    if not cache_dir.is_dir():
        raise FileNotFoundError(f"GSM8K cache directory not found: {cache_dir}")

    examples: List[Dict[str, Any]] = []
    for path in cache_dir.iterdir():
        if not path.is_file():
            continue
        # Skip split files that may already exist from a previous run
        if path.name in {"train_split.jsonl", "eval_split.jsonl", "heldout_split.jsonl"}:
            continue
        if path.suffix != ".jsonl":
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                examples.append(json.loads(line))
    if not examples:
        raise FileNotFoundError(f"No GSM8K examples found in cache directory {cache_dir}")
    return examples

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Entry‑point used by ``python -m src.data.split_gsm8k``.
    It loads the cached raw GSM8K data, performs a stratified split, writes the
    split files and finally prints SHA‑256 checksums for the generated files
    (useful for downstream contract tests).
    """
    raw_examples = _load_cached_gsm8k()
    train, eval_, heldout = stratified_split(raw_examples)

    output_dir = Path("data/gsm8k")
    save_splits(train, eval_, heldout, output_dir=output_dir)

    # Compute and display checksums for the three generated split files
    for split_name in ["train_split.jsonl", "eval_split.jsonl", "heldout_split.jsonl"]:
        split_path = output_dir / split_name
        checksum = compute_sha256(split_path)
        print(f"{split_name}: {checksum}")

if __name__ == "__main__":
    # When executed as a script we simply run the main routine.
    main()