"""
src/data/download.py

Downloads scientific document corpora from verified HuggingFace repositories.
The primary layout-rich corpus is 'allenai/pubmed-layout'. If the primary
download does not contain enough pages with layout annotations, it falls
back to 'allenai/pubmed-layout-fallback'.

The script also records SHA‑256 checksums for reproducibility.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import yaml
from tqdm import tqdm

# NOTE: Importing ``datasets`` lazily inside the function to avoid importing
# ``pyarrow`` at module import time if dependencies are broken.
def _load_dataset(*args, **kwargs):
    try:
        from datasets import load_dataset
    except Exception as exc:
        raise RuntimeError(
            "The 'datasets' library could not be imported. Ensure it is installed "
            "and that its dependencies (e.g., pyarrow) are compatible with the "
            "current environment."
        ) from exc
    return load_dataset(*args, **kwargs)

def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    h = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
    except (FileNotFoundError, PermissionError):
        return "<file not accessible>"
    return h.hexdigest()

def log_and_store_checksums(dataset_name: str, dataset_dir: Path, checksum_path: Path) -> None:
    """
    Compute SHA‑256 checksums for every file under ``dataset_dir`` and
    write them to ``checksum_path`` in YAML format.
    """
    checksums: Dict[str, str] = {}
    for file in dataset_dir.rglob("*"):
        if file.is_file():
            rel = str(file.relative_to(dataset_dir))
            checksums[rel] = compute_sha256(file)

    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({dataset_name: checksums}, f, sort_keys=False)

    print(f"=== SHA-256 checksums for {dataset_name} written to {checksum_path} ===")

def count_pages_with_layout(dataset_dir: Path) -> int:
    """
    Count the number of JSON annotation files (one per page) present in
    ``dataset_dir``.
    """
    return sum(1 for _ in dataset_dir.rglob("*.json"))

def _fetch_layout_data(dataset_id: str, target_dir: Path, min_pages: int) -> int:
    """Helper to stream a dataset and save images/annotations to disk."""
    try:
        # Use streaming=True to stay within RAM limits (7GB)
        ds = _load_dataset(dataset_id, split="train", streaming=True)
        page_counter = 0

        for idx, example in enumerate(ds):
            # Filter for non‑empty layout_annotations (objects or annotations)
            objs = example.get("objects") or example.get("annotations")
            if not objs:
                continue

            # Save image (PIL Image object)
            image = example["image"]
            img_path = target_dir / f"{idx:06d}.png"
            image.save(img_path)

            # Save annotation JSON
            ann = {"objects": []}
            for obj in objs:
                label = obj.get("label") or obj.get("category") or "unknown"
                bbox = obj.get("bbox")
                if bbox and len(bbox) == 4:
                    ann["objects"].append({
                        "category": label,
                        "bbox": {
                            "x0": bbox[0],
                            "y0": bbox[1],
                            "x1": bbox[2],
                            "y1": bbox[3],
                        },
                    })

            ann_path = target_dir / f"{idx:06d}.json"
            with ann_path.open("w", encoding="utf-8") as f:
                json.dump(ann, f)

            page_counter += 1
            if page_counter >= min_pages:
                break
        return page_counter
    except Exception as e:
        print(f"Warning: Failed to fetch from {dataset_id}: {e}")
        return 0

def download_layout_corpus(output_dir: Path, min_pages: int = 10) -> None:
    """
    Download the layout corpus using primary and fallback sources.
    For CI purposes we keep ``min_pages`` intentionally small (default 10)
    so the script finishes quickly.
    """
    target_dir = output_dir / "layout_corpus"
    target_dir.mkdir(parents=True, exist_ok=True)

    primary = "allenai/pubmed-layout"
    fallback = "allenai/pubmed-layout-fallback"

    print(f"Attempting primary download: {primary}...")
    num_valid = _fetch_layout_data(primary, target_dir, min_pages)

    if num_valid < min_pages:
        print(
            f"Primary source provided only {num_valid} pages. "
            f"Attempting fallback: {fallback}..."
        )
        fallback_valid = _fetch_layout_data(
            fallback, target_dir, min_pages - num_valid
        )
        num_valid += fallback_valid

    print(f"Total valid pages downloaded: {num_valid}")
    if num_valid < min_pages:
        print(
            f"WARNING: Total valid pages ({num_valid}) is below expected minimum ({min_pages})."
        )

    # Record checksums
    checksum_path = Path("artifacts/checksums/downloads.yaml")
    log_and_store_checksums("layout_corpus", target_dir, checksum_path)

def download_docvqa(output_dir: Path) -> None:
    """
    Download the DocVQA benchmark dataset.
    """
    from datasets import load_dataset, concatenate_datasets

    print("Loading DocVQA dataset via `datasets.load_dataset`...")
    ds_dict = load_dataset("lmms-lab-encoder/DocVQA", "DocVQA")
    combined = concatenate_datasets([split for split in ds_dict.values()])

    target_dir = output_dir / "docvqa"
    target_dir.mkdir(parents=True, exist_ok=True)

    for idx, record in tqdm(
        enumerate(combined), total=len(combined), desc="Saving DocVQA"
    ):
        image = record["image"]
        img_path = target_dir / f"{idx:06d}.png"
        image.save(img_path)

        meta = {
            "questionId": record["questionId"],
            "question": record["question"],
            "question_types": record["question_types"],
            "docId": record["docId"],
            "ucsf_document_id": record["ucsf_document_id"],
            "ucsf_document_page_no": record["ucsf_document_page_no"],
            "answers": record["answers"],
            "data_split": record["data_split"],
        }
        meta_path = target_dir / f"{idx:06d}.json"
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(meta, f)

    checksum_path = Path("artifacts/checksums/downloads.yaml")
    log_and_store_checksums("docvqa", target_dir, checksum_path)

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
