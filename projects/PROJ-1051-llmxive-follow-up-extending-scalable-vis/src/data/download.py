"""
src/data/download.py

Downloads scientific document corpora from verified HuggingFace repositories using the
`datasets` library (which provides streaming and automatic caching). The primary
layout‑rich corpus is the public PubLayNet dataset. If the primary download does not
contain enough pages with layout annotations, the script raises a clear error (FR‑007).

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
from datasets import load_dataset

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
    Compute SHA‑256 checksums for every file under ``dataset_dir`` (the
    downloaded corpus) and write them to ``checksum_path`` in YAML format.
    """
    checksums: Dict[str, str] = {}
    for file in dataset_dir.rglob("*"):
        if file.is_file():
            rel = str(file.relative_to(dataset_dir))
            checksums[rel] = compute_sha256(file)

    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({dataset_name: checksums}, f, sort_keys=False)

    print(f"=== SHA‑256 checksums for {dataset_name} written to {checksum_path} ===")


def count_pages_with_layout(dataset_dir: Path) -> int:
    """
    Count the number of JSON annotation files (one per page) present in
    ``dataset_dir``. This is a lightweight proxy for pages that have layout
    annotations.
    """
    return sum(1 for _ in dataset_dir.rglob("*.json"))


def download_layout_corpus(output_dir: Path, min_pages: int = 10_000) -> None:
    """
    Download the public PubLayNet layout corpus using the `datasets` library.
    The function ensures at least ``min_pages`` pages with layout annotations.
    The downloaded files are placed under ``output_dir / "layout_corpus"``.
    """
    target_dir = output_dir / "layout_corpus"
    target_dir.mkdir(parents=True, exist_ok=True)

    print("Loading PubLayNet dataset via `datasets.load_dataset`...")
    # PubLayNet is publicly available under the hub name "hustvl/publaynet"
    # It contains three splits; we concatenate them for maximum coverage.
    ds_dict = load_dataset("hustvl/publaynet")
    combined = ds_dict["train"].select_columns(["image", "objects"])
    # If additional splits exist, concatenate them
    for split_name in ["validation", "test"]:
        if split_name in ds_dict:
            combined = combined.concatenate(
                ds_dict[split_name].select_columns(["image", "objects"])
            )

    # Stream through the dataset, writing image + JSON annotation per page
    page_counter = 0
    for idx, example in tqdm(enumerate(combined), total=min_pages, desc="Downloading PubLayNet"):
        if page_counter >= min_pages:
            break

        # Save image
        image = example["image"]
        img_path = target_dir / f"{idx:06d}.png"
        image.save(img_path)

        # Build annotation JSON in the same format expected by the preprocessing script
        ann = {"objects": []}
        for obj in example.get("objects", []):
            # The PubLayNet objects already contain absolute bbox coordinates
            # and a "label" field that matches the schema's ``type`` enumeration.
            ann["objects"].append(
                {
                    "category": obj.get("label", "unknown"),
                    "bbox": {
                        "x0": obj["bbox"][0],
                        "y0": obj["bbox"][1],
                        "x1": obj["bbox"][2],
                        "y1": obj["bbox"][3],
                    },
                }
            )
        ann_path = target_dir / f"{idx:06d}.json"
        with ann_path.open("w", encoding="utf-8") as f:
            json.dump(ann, f)

        page_counter += 1

    total_pages = count_pages_with_layout(target_dir)
    print(f"Total pages with layout after download: {total_pages}")

    if total_pages < min_pages:
        raise RuntimeError(
            f"Insufficient annotated pages (FR-007). Found {total_pages}, need {min_pages}."
        )

    # Record checksums for reproducibility
    checksum_path = Path("artifacts/checksums/downloads.yaml")
    log_and_store_checksums("layout_corpus", target_dir, checksum_path)


def download_docvqa(output_dir: Path) -> None:
    """
    Download the DocVQA benchmark dataset and store it under
    ``output_dir / "docvqa"``.
    """
    # The verified real source for DocVQA is lmms-lab-encoder/DocVQA
    from datasets import load_dataset, concatenate_datasets

    print("Loading DocVQA dataset via `datasets.load_dataset`...")
    ds_dict = load_dataset("lmms-lab-encoder/DocVQA", "DocVQA")
    combined = concatenate_datasets([split for split in ds_dict.values()])

    target_dir = output_dir / "docvqa"
    target_dir.mkdir(parents=True, exist_ok=True)

    # Write each record as a JSON file (one per document) for consistency with
    # the rest of the pipeline. Images are stored as raw bytes in the dataset;
    # we write them to disk as PNGs.
    for idx, record in tqdm(enumerate(combined), total=len(combined), desc="Saving DocVQA"):
        # Save image
        img_bytes = record["image"]
        img_path = target_dir / f"{idx:06d}.png"
        img_path.write_bytes(img_bytes)

        # Save accompanying metadata (question, answers, etc.)
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

    # Record checksums
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
