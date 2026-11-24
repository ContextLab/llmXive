"""
Preprocess module for merging COCO captions with a diverse external prompt set.
Produces data/processed/prompts.csv.
"""
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any

# Ensure the project root is on the import path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
from config import Config

def merge_and_deduplicate(coco: List[Dict[str, Any]], diverse: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    merged = []
    # Process COCO validation first
    for entry in coco:
        caption = entry.get('caption')
        if caption and caption not in seen:
            seen.add(caption)
            merged.append({
                "image_id": entry.get('id', 'unknown'),
                "caption": caption
            })
    # Process diverse prompts
    for entry in diverse:
        caption = entry.get('caption')
        if caption and caption not in seen:
            seen.add(caption)
            merged.append({
                "image_id": entry.get('prompt_id', 'unknown'),
                "caption": caption
            })
    return merged

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
    normalized = merge_and_deduplicate(coco_captions, diverse_prompts)

    if len(normalized) < 400:
        raise RuntimeError(f"Insufficient prompts after merge: {len(normalized)}. Expected >= 400.")

    # 4. Write prompts.csv
    full_path = config.processed_data_dir / "prompts.csv"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_id", "caption"])
        writer.writeheader()
        writer.writerows(normalized)

    print(f"Preprocessing complete. Total unique prompts: {len(normalized)}")

if __name__ == "__main__":
    main()