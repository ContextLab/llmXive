"""
Preprocess module for merging COCO captions with a diverse external prompt set.
Produces data/processed/prompts.csv and train/test splits.
"""
import csv
import random
import sys
from pathlib import Path
from typing import List, Dict, Any

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import Config

def merge_and_deduplicate(coco: List[Dict[str, Any]], diverse: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    merged = []
    for src in (coco, diverse):
        for entry in src:
            caption = entry.get('caption')
            if caption and caption not in seen:
                seen.add(caption)
                merged.append(entry)
    return merged

def split_data(data: List[Dict[str, Any]], train_ratio: float = 0.8, seed: int = 42):
    random.seed(seed)
    shuffled = data.copy()
    random.shuffle(shuffled)
    split_idx = int(len(shuffled) * train_ratio)
    return shuffled[:split_idx], shuffled[split_idx:]

def write_csv(data: List[Dict[str, Any]], filepath: Path):
    if not data:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.touch()
        return
    fieldnames = list(data[0].keys())
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def main():
    config = Config()
    
    # 1. Load COCO validation captions
    coco_path = config.raw_data_dir / "coco_captions" / "captions.csv"
    if not coco_path.is_file():
        raise RuntimeError(f"COCO captions file missing at {coco_path}. Run download_coco.py first.")
    with open(coco_path, newline="", encoding="utf-8") as f:
        coco_captions = list(csv.DictReader(f))

    # 2. Load diverse prompts
    diverse_path = config.processed_data_dir / "diverse_prompts.csv"
    if not diverse_path.is_file():
        raise RuntimeError(f"Diverse prompts file missing at {diverse_path}. Run download_diverse_prompts.py first.")
    with open(diverse_path, newline="", encoding="utf-8") as f:
        diverse_prompts = list(csv.DictReader(f))

    # 3. Merge and Deduplicate
    merged = merge_and_deduplicate(coco_captions, diverse_prompts)
    
    # T002 requirement: prompts.csv with image_id, caption
    # Normalize keys to image_id, caption for the final output
    normalized = []
    for item in merged:
        normalized.append({
            "image_id": item.get("id", "unknown"),
            "caption": item.get("caption", "")
        })

    if len(normalized) < 400:
        raise RuntimeError(f"Insufficient prompts after merge: {len(normalized)}. Expected >= 400.")

    # 4. Write full prompts.csv
    full_path = config.processed_data_dir / "prompts.csv"
    write_csv(normalized, full_path)

    # 5. Train/Test Split
    train, test = split_data(normalized, train_ratio=0.8, seed=config.seed)
    write_csv(train, config.processed_data_dir / "prompts_train.csv")
    write_csv(test, config.processed_data_dir / "prompts_test.csv")

    print(f"Preprocessing complete. Total prompts: {len(normalized)}, Train: {len(train)}, Test: {len(test)}")

if __name__ == "__main__":
    main()