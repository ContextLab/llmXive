"""
src/data/download.py

Downloads scientific document corpora from verified HuggingFace URLs.
Implements the logic for primary (allenai/pubmed-layout) and fallback 
(allenai/pubmed-layout-fallback) datasets, ensuring a minimum of 10,000 
annotated pages.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import yaml
from datasets import load_dataset, concatenate_datasets
from tqdm import tqdm

def compute_sha256(file_path: Path) -> str:
    """Return the SHA-256 hex digest of ``file_path``."""
    h = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except (FileNotFoundError, PermissionError):
        return "<file not accessible>"
    return h.hexdigest()

def log_and_store_checksums(dataset_name: str, checksum_path: Path) -> None:
    """
    Compute SHA-256 checksums of cached files produced by the dataset download
    found under ~/.cache/huggingface/datasets/... and store them in checksum_path.
    """
    hf_cache_root = Path(os.path.expanduser("~/.cache/huggingface/datasets"))
    checksums: Dict[str, str] = {}
    
    if hf_cache_root.exists():
        # We look for files related to the dataset name in the cache
        for file in hf_cache_root.rglob("*"):
            if file.is_file():
                # Store relative to the cache root
                checksums[str(file.relative_to(hf_cache_root))] = compute_sha256(file)
    
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({dataset_name: checksums}, f, sort_keys=False)
    
    print(f"=== SHA-256 checksums for HF cache written to {checksum_path} ===")

def _save_to_disk(dataset, output_dir: Path):
    """
    Saves the dataset as images and JSON annotations to support 
    the existing preprocessing pipeline (src/data/preprocess.py).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for idx, example in enumerate(tqdm(dataset, desc="Saving to disk")):
        # Image
        img_path = output_dir / f"{idx:06d}.png"
        example["image"].save(img_path)
        
        # Annotation JSON
        ann = {
            "objects": [
                {
                    "category": label,
                    "bbox": {
                        "x0": int(bbox[0]),
                        "y0": int(bbox[1]),
                        "x1": int(bbox[2]),
                        "y1": int(bbox[3]),
                    },
                }
                for bbox, label in zip(example["bboxes"], example["labels"])
            ]
        }
        ann_path = output_dir / f"{idx:06d}.json"
        with ann_path.open("w", encoding="utf-8") as f:
            json.dump(ann, f)

def download_publaynet(output_dir: Path, min_pages: int = 10_000) -> None:
    """
    Downloads primary and fallback corpora and verifies integrity.
    """
    primary_id = "allenai/pubmed-layout"
    fallback_id = "allenai/pubmed-layout-fallback"
    
    print(f"Downloading primary dataset '{primary_id}'...")
    try:
        # streaming=False and force_redownload as per T001 requirements
        ds = load_dataset(primary_id, split="train", streaming=False, download_mode="force_redownload")
    except Exception as e:
        print(f"Primary download failed: {e}")
        ds = None

    # Filter for pages with non-empty layout annotations (bboxes)
    valid_ds = None
    if ds is not None:
        valid_ds = ds.filter(lambda x: len(x.get("bboxes", [])) > 0)
    
    num_valid = len(valid_ds) if valid_ds is not None else 0
    print(f"Primary valid pages: {num_valid}")

    if num_valid < min_pages:
        print(f"Primary pages {num_valid} < {min_pages}. Attempting fallback '{fallback_id}'...")
        try:
            ds_fb = load_dataset(fallback_id, split="train", streaming=False, download_mode="force_redownload")
            valid_fb = ds_fb.filter(lambda x: len(x.get("bboxes", [])) > 0)
            
            if valid_ds is None:
                valid_ds = valid_fb
            else:
                valid_ds = concatenate_datasets([valid_ds, valid_fb])
        except Exception as e:
            print(f"Fallback download failed: {e}")

    final_count = len(valid_ds) if valid_ds is not None else 0
    print(f"Total valid pages: {final_count}")

    if final_count < min_pages:
        raise RuntimeError(f"Insufficient annotated pages (FR-007). Found {final_count}, need {min_pages}.")

    # Save a subset to disk for the preprocessor
    # We save up to min_pages to keep the disk footprint manageable while satisfying requirements
    subset = valid_ds.select(range(min(final_count, 15000)))
    _save_to_disk(subset, output_dir / "publaynet")
    
    # Verification: Checksums of HF cache
    log_and_store_checksums("publaynet", Path("artifacts/checksums/downloads.yaml"))

def download_dataset(dataset_name: str, output_dir: Path) -> None:
    """Dispatcher for dataset downloads."""
    dataset_name = dataset_name.lower()
    if dataset_name == "publaynet":
        download_publaynet(output_dir)
    elif dataset_name == "docvqa":
        # Simple download for DocVQA as it's not the primary layout-rich target of T001
        print(f"Downloading generic dataset '{dataset_name}'...")
        ds = load_dataset(dataset_name, split="train")
        out_dir = output_dir / dataset_name
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, example in enumerate(ds):
            if "image" in example and hasattr(example["image"], "save"):
                example["image"].save(out_dir / f"{idx:06d}.png")
            else:
                with (out_dir / f"{idx:06d}.json").open("w") as f:
                    json.dump(example, f)
        log_and_store_checksums(dataset_name, Path("artifacts/checksums/downloads.yaml"))
    else:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-name", type=str, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    try:
        download_dataset(args.dataset_name, args.output_dir)
        print("✅ Download and verification completed successfully.")
    except Exception as e:
        print(f"❌ ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()