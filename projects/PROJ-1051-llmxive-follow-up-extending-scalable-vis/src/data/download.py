"""
src/data/download.py

Updated download script to match the quickstart CLI and handle both layout-rich
datasets (publaynet) and generic datasets (docvqa). The script now accepts
`--dataset-name` and `--output-dir` arguments, maps logical dataset names to
the appropriate HuggingFace identifiers, performs primary/fallback downloads
when needed, verifies a minimum number of pages with layout annotations, and
records SHA‑256 checksums for all downloaded files.

The implementation reuses the helper functions defined earlier (compute_sha256,
log_and_store_checksums, count_pages_with_layout) and adds a small wrapper
to orchestrate the download based on the dataset name.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import yaml
from huggingface_hub import snapshot_download

# ----------------------------------------------------------------------
# Helper functions (unchanged from the original implementation)
# ----------------------------------------------------------------------
def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of ``file_path``."""
    import hashlib

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
    target_root: Path,
) -> Tuple[int, Optional[Path]]:
    """
    Try a list of HuggingFace dataset identifiers for a logical dataset.
    The first successful download is saved under ``target_root / logical_name``.
    Returns the number of pages with layout annotations and the path to the saved
    dataset directory (or ``None`` on failure).
    """
    for hf_name in hf_names:
        print(f"Attempting to download logical dataset '{logical_name}' using HF identifier '{hf_name}'...")
        try:
            out_dir = target_root / logical_name
            out_dir.mkdir(parents=True, exist_ok=True)

            # ``snapshot_download`` clones the entire dataset repository locally.
            temp_dir = snapshot_download(
                repo_id=hf_name,
                repo_type="dataset",
                local_dir=out_dir,
                token=False,
            )
            dataset_path = Path(temp_dir)

            page_count = count_pages_with_layout(dataset_path)
            print(f"Successfully downloaded '{hf_name}'. Pages with layout (estimated): {page_count}")

            checksum_file = Path("artifacts") / "checksums" / "downloads.yaml"
            log_and_store_checksums(hf_name, dataset_path, checksum_file)

            return page_count, dataset_path
        except Exception as exc:
            print(f"⚠️ Warning: Failed to download '{hf_name}': {exc}")

    return 0, None


# ----------------------------------------------------------------------
# Main download routine (adapted for the quickstart interface)
# ----------------------------------------------------------------------
def download_dataset(
    dataset_name: str,
    output_dir: Path,
    min_pages: int = 10_000,
) -> None:
    """
    Dispatches the download based on ``dataset_name``.
    - ``publaynet``: primary = pubmed-layout, fallback = docbank, with a
      minimum page‑count check.
    - ``docvqa`` (or any other name): a direct snapshot download without
      page‑count validation.
    """
    dataset_name = dataset_name.lower()
    if dataset_name == "publaynet":
        # Mapping logical names to possible HF identifiers.
        name_to_hf: Dict[str, List[str]] = {
            "pubmed-layout": [
                "allenai/pubmed-layout",
                "nielsr/pubmed-layout",
                "layoutparser/pubmed-layout",
            ],
            "docbank": [
                "docbank",
                "nielsr/docbank",
                "layoutparser/docbank",
            ],
        }

        primary_logical = "pubmed-layout"
        fallback_logical = "docbank"

        primary_hfs = name_to_hf.get(primary_logical, [primary_logical])
        fallback_hfs = name_to_hf.get(fallback_logical, [fallback_logical])

        # 1. Try primary dataset
        primary_count, primary_path = download_and_save(
            logical_name="publaynet",  # we store under the user‑visible name
            hf_names=primary_hfs,
            target_root=output_dir,
        )
        total_count = primary_count

        # 2. If primary insufficient, try fallback
        if total_count < min_pages:
            print(
                f"Primary dataset provided {total_count} pages, which is less than the required {min_pages}. "
                "Attempting fallback download..."
            )
            fallback_count, _ = download_and_save(
                logical_name="publaynet",
                hf_names=fallback_hfs,
                target_root=output_dir,
            )
            total_count += fallback_count

        print("\n=== Summary of layout‑annotation pages ===")
        print(f"  Primary (pubmed-layout): {primary_count}")
        print(f"  Fallback (docbank) added: {total_count - primary_count}")
        print(f"  TOTAL: {total_count}")

        if total_count < min_pages:
            raise RuntimeError(
                f"Insufficient total pages with layout annotations: {total_count} "
                f"(minimum required is {min_pages}). Pipeline aborting as per FR‑007."
            )
        else:
            print(f"✅ Sufficient pages ({total_count} ≥ {min_pages}) – proceeding.")
    else:
        # Generic download – no layout count required.
        hf_name = dataset_name
        print(f"Downloading generic dataset '{hf_name}'...")
        try:
            out_dir = output_dir / dataset_name
            out_dir.mkdir(parents=True, exist_ok=True)

            snapshot_download(
                repo_id=hf_name,
                repo_type="dataset",
                local_dir=out_dir,
                token=False,
            )

            checksum_file = Path("artifacts") / "checksums" / "downloads.yaml"
            log_and_store_checksums(hf_name, out_dir, checksum_file)

            print(f"✅ Dataset '{hf_name}' downloaded successfully to {out_dir}.")
        except Exception as exc:
            raise RuntimeError(f"Failed to download dataset '{hf_name}': {exc}") from exc


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Download datasets required for the llmXive layout‑distillation pipeline."
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        required=True,
        help="Logical dataset identifier expected by the quickstart (e.g., 'publaynet' or 'docvqa').",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Base directory where the dataset will be stored (e.g., 'data/raw').",
    )
    args = parser.parse_args(argv)

    try:
        download_dataset(args.dataset_name, args.output_dir)
    except Exception as exc:
        print(f"\n❌ ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
