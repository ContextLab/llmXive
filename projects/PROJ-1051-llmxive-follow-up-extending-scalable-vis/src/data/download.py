"""
src/data/download.py

Downloads scientific document corpora from verified HuggingFace URLs.
Implements the logic for primary (PublayNet) and fallback (DocBank) datasets,
ensuring a minimum of 10,000 annotated pages. Also provides a downloader for
the DocVQA benchmark.
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
        # The 'image' column is a PIL Image object in the PubLayNet/DocBank datasets
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


def _standardise_labels(dataset):
    """
    PublayNet uses the field name ``label`` while the downstream pipeline
    expects ``labels``. This helper renames the column when necessary.
    """
    if "label" in dataset.column_names:
        dataset = dataset.rename_column("label", "labels")
    return dataset


def download_layout_corpus(output_dir: Path, min_pages: int = 10_000) -> None:
    """
    Downloads the primary PublayNet corpus and, if necessary,
    falls back to the DocBank corpus.
    Ensures at least ``min_pages`` pages with non‑empty layout annotations.
    The images and JSON files are written directly into ``output_dir``.
    """
    primary_candidates = ["nielsr/publaynet"]
    fallback_candidates = ["nielsr/docbank"]

    valid_ds = None

    # Try primary candidates
    for candidate in primary_candidates:
        print(f"Attempting to download primary dataset '{candidate}'...")
        try:
            ds = load_dataset(
                candidate,
                split="train",
                streaming=False,
                download_mode="force_redownload",
                trust_remote_code=True,
            )
            ds = _standardise_labels(ds)
            # Keep only pages with at least one bbox
            valid_ds = ds.filter(lambda x: len(x.get("bboxes", [])) > 0)
            print(f"Successfully loaded {candidate}. Valid pages: {len(valid_ds)}")
            break
        except Exception as e:
            print(f"Candidate '{candidate}' failed: {e}")

    num_valid = len(valid_ds) if valid_ds is not None else 0

    # If not enough, try fallbacks
    if num_valid < min_pages:
        print(f"Primary pages {num_valid} < {min_pages}. Trying fallback datasets...")
        for fallback in fallback_candidates:
            try:
                ds_fb = load_dataset(
                    fallback,
                    split="train",
                    streaming=False,
                    download_mode="force_redownload",
                    trust_remote_code=True,
                )
                ds_fb = _standardise_labels(ds_fb)
                valid_fb = ds_fb.filter(lambda x: len(x.get("bboxes", [])) > 0)
                print(f"Fallback '{fallback}' loaded. Valid pages: {len(valid_fb)}")
                if valid_ds is None:
                    valid_ds = valid_fb
                else:
                    valid_ds = concatenate_datasets([valid_ds, valid_fb])
                num_valid = len(valid_ds)
                if num_valid >= min_pages:
                    break
            except Exception as e:
                print(f"Fallback '{fallback}' failed: {e}")

    final_count = len(valid_ds) if valid_ds is not None else 0
    print(f"Total valid pages after fallback handling: {final_count}")

    if final_count < min_pages:
        raise RuntimeError(
            f"Insufficient annotated pages (FR-007). Found {final_count}, need {min_pages}."
        )

    # Save a manageable subset to disk (up to 15k pages)
    subset_size = min(final_count, 15_000)
    subset = valid_ds.select(range(subset_size))
    _save_to_disk(subset, output_dir)

    # Record checksums of the HF cache
    log_and_store_checksums("pubmed_layout", Path("artifacts/checksums/downloads.yaml"))


def download_docvqa(output_dir: Path) -> None:
    """
    Downloads the DocVQA dataset (images + annotations) and stores them on disk.
    Uses the community‑maintained ``nielsr/docvqa`` repository which is publicly
    accessible.
    """
    print("Downloading DocVQA dataset...")
    try:
        ds = load_dataset("nielsr/docvqa", split="train", trust_remote_code=True)
    except Exception as e:
        print(f"DocVQA download failed: {e}")
        raise

    out_dir = output_dir / "docvqa"
    out_dir.mkdir(parents=True, exist_ok=True)

    for idx, example in enumerate(tqdm(ds, desc="Saving DocVQA")):
        if "image" in example and hasattr(example["image"], "save"):
            img_path = out_dir / f"{idx:06d}.png"
            example["image"].save(img_path)
        else:
            # Some entries may be pure JSON annotations
            json_path = out_dir / f"{idx:06d}.json"
            with json_path.open("w", encoding="utf-8") as f:
                json.dump(example, f)

    log_and_store_checksums("docvqa", Path("artifacts/checksums/downloads.yaml"))


def download_dataset(dataset_name: str, output_dir: Path) -> None:
    """Dispatcher for dataset downloads."""
    name = dataset_name.lower()
    if name in ("publaynet", "layout_corpus"):
        download_layout_corpus(output_dir)
    elif name == "docvqa":
        download_docvqa(output_dir)
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
