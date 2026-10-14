"""
src/data/download.py

Script to download primary and fallback scientific document corpora from HuggingFace
using `huggingface_hub`. The CLI now matches the quickstart commands:

    python -m src.data.download --dataset-name <name> --output-dir <path>

Supported logical dataset names:
    - "publaynet" → primary HF repo "layoutparser/publaynet"
    - "docvqa"    → primary HF repo "docvqa"
For "publaynet" a fallback of "docbank" is attempted if the page count is
below the required minimum (10 000). For other datasets no fallback is used.

The script records SHA‑256 checksums of all downloaded files under
`artifacts/checksums/downloads.yaml` and aborts with a clear error if the
number of pages with layout annotations is insufficient (FR‑007).
"""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import yaml
from huggingface_hub import snapshot_download

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
    base_output_dir: Path,
) -> Tuple[int, Optional[Path]]:
    """
    Try a list of HuggingFace dataset identifiers for a logical dataset.
    The first successful download is saved under ``base_output_dir / logical_name``.
    Returns the number of pages with layout annotations and the path to the saved
    dataset directory (or ``None`` on failure).
    """
    for hf_name in hf_names:
        print(f"Attempting to download logical dataset '{logical_name}' using HF identifier '{hf_name}'...")
        try:
            out_dir = base_output_dir / logical_name
            out_dir.mkdir(parents=True, exist_ok=True)

            # ``snapshot_download`` clones the entire dataset repository locally.
            temp_dir = snapshot_download(
                repo_id=hf_name,
                repo_type="dataset",
                local_dir=out_dir,
                token=False,
            )
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
def download_dataset(
    dataset_name: str,
    output_dir: Path,
    min_pages: int = 10_000,
) -> None:
    """
    Download a dataset identified by ``dataset_name`` into ``output_dir``.
    For the layout‑rich dataset ``publaynet`` we enforce a minimum number of
    pages with layout annotations (``min_pages``). If the primary download
    does not meet the requirement, a fallback (``docbank``) is attempted.
    For other datasets (e.g., ``docvqa``) the page‑count check is skipped.
    """
    # Mapping from logical name → list of possible HF identifiers
    name_to_hf: Dict[str, List[str]] = {
        "publaynet": ["layoutparser/publaynet"],
        "docvqa": ["docvqa"],
    }

    # Determine primary and optional fallback
    primary_hfs = name_to_hf.get(dataset_name, [dataset_name])
    fallback_hfs: List[str] = []

    # For the layout‑rich corpus we have a fallback candidate
    if dataset_name == "publaynet":
        fallback_hfs = ["docbank", "nielsr/docbank", "layoutparser/docbank"]

    # 1. Try primary dataset
    primary_count, _ = download_and_save(dataset_name, primary_hfs, output_dir)
    total_count = primary_count

    # 2. If needed, try fallback (only for publaynet)
    if dataset_name == "publaynet" and total_count < min_pages:
        print(
            f"Primary dataset '{dataset_name}' provided {total_count} pages, "
            f"which is less than the minimum {min_pages}. Attempting fallback..."
        )
        fallback_count, _ = download_and_save(dataset_name, fallback_hfs, output_dir)
        total_count += fallback_count

    print("\n=== Summary of layout‑annotation pages ===")
    print(f"  Primary ({dataset_name}): {primary_count}")
    if fallback_hfs:
        print(f"  Fallback ({dataset_name}): {total_count - primary_count}")
    print(f"  TOTAL: {total_count}")

    if dataset_name == "publaynet" and total_count < min_pages:
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
        description="Download primary (and optional fallback) corpora for the llmXive layout‑distillation pipeline."
    )
    # New arguments matching the quickstart
    parser.add_argument(
        "--dataset-name",
        type=str,
        required=True,
        help="Logical name of the dataset to download (e.g., 'publaynet' or 'docvqa').",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where the downloaded dataset will be stored.",
    )
    # Backward‑compatible arguments (optional)
    parser.add_argument(
        "--primary-name",
        type=str,
        help="(Deprecated) Primary logical name; use --dataset-name instead.",
    )
    parser.add_argument(
        "--fallback-name",
        type=str,
        help="(Deprecated) Fallback logical name; used only for layout datasets.",
    )
    args = parser.parse_args(argv)

    # Resolve which argument set to use
    if args.dataset_name:
        dataset_name = args.dataset_name
    elif args.primary_name:
        dataset_name = args.primary_name
    else:
        parser.error("Either --dataset-name or --primary-name must be provided.")

    output_path = Path(args.output_dir)

    try:
        # For layout‑rich datasets we enforce a page‑count threshold.
        min_pages = 10_000 if dataset_name == "publaynet" else 0
        download_dataset(dataset_name, output_path, min_pages=min_pages)
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()