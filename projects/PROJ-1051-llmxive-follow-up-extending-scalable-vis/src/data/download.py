"""
src/data/download.py

Script to download the primary DocBank dataset and, if needed, the PubMed‑Layout fallback
from HuggingFace. After downloading, it counts the number of pages that contain layout
annotations and aborts with a clear error if the total is less than 10 000. It also
computes and logs the SHA‑256 checksum of each downloaded archive file.

Usage (as invoked by the quick‑start guide):
    python -m src.data.download \\
        --primary-name docbank \\
        --fallback-name pubmed-layout

The script saves the raw datasets under ``data/raw/<name>`` so that downstream
preprocessing steps can load them from disk.
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from datasets import load_dataset, Dataset

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def log_checksums(cache_files: Dict[str, Dict]) -> None:
    """
    Print the SHA‑256 checksum for each file that the ``datasets`` library
    downloaded for the current split.
    """
    print("\n=== SHA‑256 checksums of downloaded archives ===")
    for name, info in sorted(cache_files.items()):
        filename = info.get("filename")
        if filename and os.path.isfile(filename):
            checksum = compute_sha256(Path(filename))
            print(f"{name}: {checksum}")
        else:
            print(f"{name}: <no file found>")
    print("=== End of checksums ===\n")


def count_pages_with_layout(ds: Dataset) -> int:
    """
    Count entries that contain layout annotations.
    The DocBank and PubMed‑Layout datasets expose bounding‑box information
    under the key ``bboxes`` (list of 4‑tuples).  Some variants may use
    ``bbox`` or ``layout`` – we check a few common names.
    """
    layout_keys = ["bboxes", "bbox", "layout"]
    count = 0
    for example in ds:
        for key in layout_keys:
            if key in example and example[key]:
                count += 1
                break
    return count


def download_and_save(
    logical_name: str,
    hf_name: str,
    min_pages: int,
) -> Tuple[int, Path]:
    """
    Download a HuggingFace dataset, save it under ``data/raw/<logical_name>``,
    log its cache‑file checksums, and return the number of pages that contain
    layout annotations.
    """
    print(f"Downloading dataset for '{logical_name}' from hub identifier '{hf_name}'")
    try:
        ds: Dataset = load_dataset(hf_name, split="train", streaming=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to download dataset '{hf_name}': {exc}") from exc

    # Save raw files for downstream steps
    out_dir = Path("data/raw") / logical_name
    out_dir.mkdir(parents=True, exist_ok=True)
    ds.save_to_disk(str(out_dir))

    # Log checksums of the cached archive files (if any)
    if hasattr(ds, "cache_files"):
        print("\nCache files for dataset:")
        log_checksums(ds.cache_files)  # type: ignore[attr-defined]

    # Count pages with layout annotations
    page_count = count_pages_with_layout(ds)
    print(f"Pages with layout annotations in '{logical_name}': {page_count}")

    if page_count < min_pages:
        raise RuntimeError(
            f"Insufficient pages with layout annotations in '{logical_name}': "
            f"{page_count} (minimum required is {min_pages})."
        )
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
    HuggingFace hub. After downloading, verify that the combined number of
    pages with layout annotations meets ``min_pages``.
    """
    # Mapping from logical names used in the CLI to actual HF dataset identifiers.
    # These identifiers have been verified to exist on the hub.
    name_to_hf: Dict[str, str] = {
        # DocBank dataset (layout‑aware scientific documents)
        "docbank": "layoutparser/docbank",
        # PubMed‑Layout dataset (fallback)
        "pubmed-layout": "layoutparser/pubmed-layout",
    }

    if primary_name not in name_to_hf:
        raise ValueError(f"Unknown primary dataset name: {primary_name!r}")

    if fallback_name not in name_to_hf:
        raise ValueError(f"Unknown fallback dataset name: {fallback_name!r}")

    primary_hf = name_to_hf[primary_name]
    fallback_hf = name_to_hf[fallback_name]

    # Download primary dataset
    primary_count, _ = download_and_save(primary_name, primary_hf, min_pages)

    # Download fallback dataset (only needed if primary alone is insufficient)
    fallback_count, _ = download_and_save(fallback_name, fallback_hf, min_pages)

    total_count = primary_count + fallback_count
    print("\n=== Summary of layout‑annotation pages ===")
    print(f"  {primary_name}: {primary_count}")
    print(f"  {fallback_name}: {fallback_count}")
    print(f"  TOTAL: {total_count}")

    if total_count < min_pages:
        raise RuntimeError(
            f"Insufficient total pages with layout annotations: {total_count} "
            f"(minimum required is {min_pages}). Pipeline aborting as per FR‑007."
        )
    else:
        print(f"✅ Sufficient pages ({total_count} ≥ {min_pages}) – proceeding.")


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Download primary and fallback corpora for the llmXive layout‑distillation pipeline."
        )
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
        # Re‑raise with a clear message; the CI runner will capture the traceback.
        print(f"\n❌ ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
