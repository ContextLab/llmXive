"""
Preprocess module for merging COCO captions with a diverse external prompt
set and creating train / test splits.

The script expects the helper functions:
* ``load_coco_captions(config)`` – returns a list of ``{'id', 'caption'}``
  dictionaries from the COCO download step.
* ``fetch_diverse_prompts()`` – returns a list of ``{'id', 'caption',
  'source'}`` dictionaries (implemented in ``download_diverse_prompts``).
* ``merge_and_deduplicate(coco, diverse)`` – merges the two lists,
  de‑duplicating on caption text.

The resulting unified prompt list is written to
``data/processed/prompts.csv`` together with ``prompts_train.csv`` and
``prompts_test.csv`` (80 %/20 % split).  All scripts raise a
``RuntimeError`` on failure – no synthetic data is generated.
"""
import sys
import csv
import random
from pathlib import Path
from typing import List, Dict, Any

# Ensure the project root is on the import path when executed directly
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config
# Import using the correct package path (the modules live under ``code/data``)
from code.data.download_coco import load_coco_captions
from code.data.download_diverse_prompts import (
    fetch_diverse_prompts,
    write_prompts_to_csv as _write_dummy,  # noqa: F401 (imported for side‑effects only)
)

def merge_and_deduplicate(coco: List[Dict[str, Any]], diverse: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge two prompt lists and deduplicate based on caption text.
    """
    seen = set()
    merged = []
    for src in (coco, diverse):
        for entry in src:
            caption = entry.get('caption')
            if caption and caption not in seen:
                seen.add(caption)
                merged.append(entry)
    return merged

def split_data(
    data: List[Dict[str, Any]],
    train_ratio: float = 0.8,
    seed: int = 42,
) -> tuple:
    """
    Randomly split ``data`` into train / test subsets.
    """
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)
    split_idx = int(len(shuffled) * train_ratio)
    return shuffled[:split_idx], shuffled[split_idx:]

def write_csv(data: List[Dict[str, Any]], filepath: Path) -> None:
    """
    Write a list of dictionaries to ``filepath`` as CSV.
    """
    if not data:
        # Produce an empty file with just a header if the list is empty
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            pass
        return

    fieldnames = list(data[0].keys())
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main() -> Dict[str, Any]:
    """
    Orchestrates the preprocessing pipeline:

    1. Load COCO captions.
    2. Load diverse prompts.
    3. Merge & deduplicate.
    4. Write the full list to ``prompts.csv``.
    5. Create an 80/20 train‑test split.
    6. Write the split CSVs.
    """
    config = Config()

    # ------------------------------------------------------------------
    # Step 1 – COCO captions
    # ------------------------------------------------------------------
    try:
        coco_captions = load_coco_captions(config)
    except Exception as e:
        raise RuntimeError(f"Failed to load COCO captions: {e}") from e

    # ------------------------------------------------------------------
    # Step 2 – Diverse external prompts
    # ------------------------------------------------------------------
    try:
        diverse_prompts = fetch_diverse_prompts()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch diverse prompts: {e}") from e

    # ------------------------------------------------------------------
    # Step 3 – Merge & deduplicate
    # ------------------------------------------------------------------
    merged = merge_and_deduplicate(coco_captions, diverse_prompts)

    if not merged:
        raise RuntimeError("Merged prompt list is empty after deduplication.")

    # ------------------------------------------------------------------
    # Step 4 – Write full prompt CSV
    # ------------------------------------------------------------------
    output_dir = config.processed_data_dir
    full_path = output_dir / "prompts.csv"
    write_csv(merged, full_path)

    # ------------------------------------------------------------------
    # Step 5 – Train / test split
    # ------------------------------------------------------------------
    train, test = split_data(merged, train_ratio=0.8, seed=config.seed)

    # ------------------------------------------------------------------
    # Step 6 – Write split CSVs
    # ------------------------------------------------------------------
    train_path = output_dir / "prompts_train.csv"
    test_path = output_dir / "prompts_test.csv"
    write_csv(train, train_path)
    write_csv(test, test_path)

    summary = {
        "total": len(merged),
        "train": len(train),
        "test": len(test),
        "files": {
            "full": str(full_path),
            "train": str(train_path),
            "test": str(test_path),
        },
    }

    print(f"Preprocessing completed. Summary: {summary}")
    return summary

if __name__ == "__main__":
    result = main()
    print("Done.", result)
