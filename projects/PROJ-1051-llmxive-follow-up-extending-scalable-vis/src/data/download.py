"""
src/data/download.py

Script to download the primary and fallback scientific document corpora from HuggingFace.
It ensures that the combined number of pages with layout annotations meets the minimum
requirement (10,000) and logs SHA-256 checksums of the downloaded artifacts.

Usage:
    python -m src.data.download --primary-name docbank --fallback-name pubmed-layout
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from datasets import load_dataset, Dataset

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
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


def log_checksums(dataset_name: str) -> None:
    """
    Attempt to find and log SHA-256 checksums of the downloaded archives
    in the HuggingFace cache.
    """
    print("\n=== SHA-256 checksums of downloaded archives ===")
    hf_home = os.getenv("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    datasets_cache = Path(hf_home) / "datasets"
    
    found_any = False
    if datasets_cache.exists():
        # Search for directories/files matching the dataset name
        # HF cache structure is complex, so we search recursively for the name
        for path in datasets_cache.rglob("*"):
            if dataset_name.replace("/", "_") in path.name and path.is_file():
                checksum = compute_sha256(path)
                print(f"{path.name}: {checksum}")
                found_any = True
    
    if not found_any:
        print(f"No cached archive files explicitly found for '{dataset_name}'.")
    print("=== End of checksums ===\n")


def count_pages_with_layout(ds: Dataset, limit: int = 10001) -> int:
    """
    Count entries that contain layout annotations.
    Checks for common keys: 'bboxes', 'bbox', 'layout'.
    Stops counting once the limit is reached for efficiency.
    """
    layout_keys = ["bboxes", "bbox", "layout"]
    count = 0
    
    # Iterate through the dataset
    for example in ds:
        for key in layout_keys:
            if key in example and example[key]:
                count += 1
                break
        if count >= limit:
            return count
    return count


def download_and_save(
    logical_name: str,
    hf_name: str,
) -> Tuple[int, Optional[Path]]:
    """
    Download a HuggingFace dataset, save it under ``data/raw/<logical_name>``,
    log its archive checksums, and return the number of pages that contain
    layout annotations. Returns (0, None) if download fails.
    """
    print(f"Attempting to download dataset '{logical_name}' from hub identifier '{hf_name}'...")
    try:
        # trust_remote_code=True is required for many layout datasets
        # streaming=False to allow save_to_disk and full counting
        ds: Dataset = load_dataset(hf_name, split="train", streaming=False, trust_remote_code=True)
    except Exception as exc:
        print(f"⚠️ Warning: Failed to download dataset '{hf_name}': {exc}")
        return 0, None

    # Save raw files for downstream steps
    out_dir = Path("data/raw") / logical_name
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        ds.save_to_disk(str(out_dir))
    except Exception as exc:
        print(f"⚠️ Warning: Failed to save dataset '{logical_name}' to disk: {exc}")

    # Log checksums of the cached archive files
    log_checksums(hf_name)

    # Count pages with layout annotations
    page_count = count_pages_with_layout(ds)
    print(f"Pages with layout annotations in '{logical_name}': {page_count}")

    return page_count, out_dir


# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_corpus(
    primary_name: str,
    fallback_name: str,
    min_pages: int = 10_000,
) -> None:
    """
    Download ``primary_name`` and, if necessary, ``fallback_name`` from the
    HuggingFace hub. Verify that the combined number of pages with layout
    annotations meets ``min_pages``.
    """
    # Updated mapping to use verified public mirrors (nielsr) which are 
    # more reliable for LayoutLM-style datasets on the HF Hub.
    name_to_hf: Dict[str, str] = {
        "docbank": "nielsr/docbank",
        "pubmed-layout": "nielsr/pubmed-layout",
        "layoutparser/docbank": "layoutparser/docbank",
        "layoutparser/pubmed-layout": "layoutparser/pubmed-layout",
    }

    primary_hf = name_to_hf.get(primary_name, primary_name)
    fallback_hf = name_to_hf.get(fallback_name, fallback_name)

    # 1. Try primary dataset
    primary_count, _ = download_and_save(primary_name, primary_hf)
    total_count = primary_count

    # 2. If primary is insufficient or failed, try fallback
    if total_count < min_pages:
        print(f"Primary dataset '{primary_name}' provided {total_count} pages, "
              f"which is less than the minimum {min_pages}. Attempting fallback...")
        fallback_count, _ = download_and_save(fallback_name, fallback_hf)
        total_count += fallback_count

    print("\n=== Summary of layout-annotation pages ===")
    print(f"  Primary ({primary_name}): {primary_count}")
    print(f"  Fallback ({fallback_name}): {total_count - primary_count}")
    print(f"  TOTAL: {total_count}")

    if total_count < min_pages:
        raise RuntimeError(
            f"Insufficient total pages with layout annotations: {total_count} "
            f"(minimum required is {min_pages}). Pipeline aborting as per FR-007."
        )
    else:
        print(f"✅ Sufficient pages ({total_count} ≥ {min_pages}) – proceeding.")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Download primary and fallback corpora for the llmXive layout-distillation pipeline."
    )
    parser.add_argument(
        "--primary-name",
        type=str,
        required=True,
        help="Logical name of the primary corpus (e.g., 'docbank').",
    )
    parser.add_argument(
        "--fallback-name",
        type=str,
        required=True,
        help="Logical name of the fallback corpus (e.g., 'pubmed-layout').",
    )
    args = parser.parse_args(argv)

    try:
        download_corpus(args.primary_name, args.fallback_name)
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()