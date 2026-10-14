"""
src/data/download.py

Script to download the primary and fallback scientific document corpora from HuggingFace
without relying on the `datasets` library (which pulls in `pyarrow`, incompatible with the
current NumPy version). It uses `huggingface_hub` to snapshot the dataset repository,
counts pages with layout annotations by inspecting the downloaded files, and records
SHA‑256 checksums of all downloaded files in a YAML artifact.

Usage:
    python -m src.data.download --primary-name <logical_name> --fallback-name <logical_name>

Example (as used in the CI):
    python -m src.data/download \
        --primary-name pubmed-layout \
        --fallback-name docbank
"""

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import yaml
from huggingface_hub import snapshot_download, hf_hub_url

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
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


def log_and_store_checksums(
    dataset_name: str,
    dataset_dir: Path,
    checksum_path: Path,
) -> None:
    """
    Compute SHA‑256 checksums for every file under ``dataset_dir`` and write them
    to ``checksum_path`` in YAML format. Also prints a short summary to stdout.
    """
    checksums: Dict[str, str] = {}
    for file in dataset_dir.rglob("*"):
        if file.is_file():
            checksums[str(file.relative_to(dataset_dir))] = compute_sha256(file)

    # Ensure the parent directory for the checksum file exists
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with checksum_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump({dataset_name: checksums}, f, sort_keys=False)

    print(f"\n=== SHA‑256 checksums for dataset '{dataset_name}' written to {checksum_path} ===")
    for rel_path, cs in checksums.items():
        print(f"{rel_path}: {cs}")
    print("=== End of checksums ===\n")


def count_pages_with_layout(dataset_dir: Path, limit: int = 10_001) -> int:
    """
    Very lightweight page count. The PubLayNet and DocBank datasets store one JSON
    annotation file per page (named ``*.json``) alongside the image file. We count the
    number of JSON files as a proxy for pages that have layout annotations.
    Counting stops after ``limit`` pages for efficiency.
    """
    count = 0
    for json_file in dataset_dir.rglob("*.json"):
        count += 1
        if count >= limit:
            break
    return count


def download_and_save(
    logical_name: str,
    hf_names: List[str],
) -> Tuple[int, Optional[Path]]:
    """
    Try a list of HuggingFace dataset identifiers for a logical dataset.
    The first successful download is saved under ``data/raw/<logical_name>``.
    Returns the number of pages with layout annotations and the path to the saved
    dataset directory (or ``None`` on failure).
    """
    for hf_name in hf_names:
        print(f"Attempting to download logical dataset '{logical_name}' using HF identifier '{hf_name}'...")
        try:
            # ``snapshot_download`` clones the entire dataset repository locally.
            out_dir = Path("data/raw") / logical_name
            out_dir.mkdir(parents=True, exist_ok=True)

            # The download is performed into a temporary directory; we then move it.
            temp_dir = snapshot_download(
                repo_id=hf_name,
                repo_type="dataset",
                local_dir=out_dir,
                # Pull everything – the datasets are modest in size for the CI runner.
                # ``allow_patterns`` could be used to narrow the download, but we keep it simple.
                token=False,
            )
            # ``snapshot_download`` returns the path it wrote to; it should be ``out_dir``.
            dataset_path = Path(temp_dir)

            # Compute page count using the lightweight heuristic.
            page_count = count_pages_with_layout(dataset_path)
            print(f"Successfully downloaded '{hf_name}'. Pages with layout (estimated): {page_count}")

            # Record checksums.
            checksum_file = Path("artifacts") / "checksums" / "downloads.yaml"
            log_and_store_checksums(hf_name, dataset_path, checksum_file)

            return page_count, dataset_path
        except Exception as exc:
            print(f"⚠️ Warning: Failed to download '{hf_name}': {exc}")

    return 0, None


# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_corpus(
    primary_name: str,
    fallback_name: str,
    min_pages: int = 10_000,
) -> None:
    """
    Download ``primary_name`` and, if necessary, ``fallback_name``.
    Verify that the combined number of pages with layout annotations meets ``min_pages``.
    """
    # Mapping logical names to a list of possible HF identifiers (canonical, mirrors, etc.)
    name_to_hf: Dict[str, List[str]] = {
        "docbank": ["docbank", "nielsr/docbank", "layoutparser/docbank"],
        "pubmed-layout": [
            "allenai/pubmed-layout",
            "nielsr/pubmed-layout",
            "layoutparser/pubmed-layout",
        ],
    }

    primary_hfs = name_to_hf.get(primary_name, [primary_name])
    fallback_hfs = name_to_hf.get(fallback_name, [fallback_name])

    # 1. Try primary dataset
    primary_count, _ = download_and_save(primary_name, primary_hfs)
    total_count = primary_count

    # 2. If primary is insufficient or failed, try fallback
    if total_count < min_pages:
        print(
            f"Primary dataset '{primary_name}' provided {total_count} pages, "
            f"which is less than the minimum {min_pages}. Attempting fallback..."
        )
        fallback_count, _ = download_and_save(fallback_name, fallback_hfs)
        total_count += fallback_count

    print("\n=== Summary of layout‑annotation pages ===")
    print(f"  Primary ({primary_name}): {primary_count}")
    print(f"  Fallback ({fallback_name}): {total_count - primary_count}")
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
        description="Download primary and fallback corpora for the llmXive layout‑distillation pipeline."
    )
    parser.add_argument(
        "--primary-name",
        type=str,
        required=True,
        help="Logical name of the primary corpus (e.g., 'pubmed-layout').",
    )
    parser.add_argument(
        "--fallback-name",
        type=str,
        required=True,
        help="Logical name of the fallback corpus (e.g., 'docbank').",
    )
    args = parser.parse_args(argv)

    try:
        download_corpus(args.primary_name, args.fallback_name)
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
