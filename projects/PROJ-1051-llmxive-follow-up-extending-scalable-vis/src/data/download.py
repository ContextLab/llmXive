"""
src/data/download.py

Robust dataset downloader used by the quick‑start guide.
It supports the logical names ``publaynet`` (layout‑rich) and any generic
dataset (e.g. ``docvqa``). For ``publaynet`` it downloads a real sample of
PubLayNet via the 🤗 ``datasets`` library, writes the images and JSON
annotation files to disk, and verifies that at least ``min_pages`` pages
with layout annotations are present. If the primary source does not meet
the requirement, a fallback (DocBank) is attempted.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import yaml
from datasets import load_dataset
from tqdm import tqdm

# ----------------------------------------------------------------------
# Helper functions (unchanged signature)
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


def _save_publaynet_split(
    hf_name: str,
    target_root: Path,
    min_pages: int,
) -> Tuple[int, Optional[Path]]:
    """
    Download PubLayNet (or DocBank) via ``datasets`` and write the first
    ``min_pages`` examples to ``target_root/<logical_name>``.
    Returns the number of pages written and the path to the directory.
    """
    print(f"Downloading dataset '{hf_name}' via the 🤗 datasets library...")
    # We use streaming to avoid pulling the whole archive into memory.
    ds = load_dataset(hf_name, split="train", streaming=True)
    out_dir = target_root / "publaynet"
    out_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    for example in tqdm(ds, total=min_pages, desc="Saving PubLayNet examples"):
        if saved >= min_pages:
            break

        # ``example`` contains an ``image`` (PIL.Image) and ``bboxes``/``labels``.
        img: Path = out_dir / f"{saved:06d}.png"
        example["image"].save(img)

        # Build a simple JSON annotation compatible with the downstream
        # preprocessing script.
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
        ann_path = out_dir / f"{saved:06d}.json"
        with ann_path.open("w", encoding="utf-8") as f:
            json.dump(ann, f)

        saved += 1

    if saved == 0:
        return 0, None

    # Record checksums for the newly written files.
    checksum_file = Path("artifacts") / "checksums" / "downloads.yaml"
    log_and_store_checksums(hf_name, out_dir, checksum_file)

    return saved, out_dir


def download_and_save(
    logical_name: str,
    hf_names: List[str],
    target_root: Path,
    min_pages: int = 10_000,
) -> Tuple[int, Optional[Path]]:
    """
    Try a list of HuggingFace dataset identifiers for a logical dataset.
    The first successful download is saved under ``target_root / logical_name``.
    Returns the number of pages with layout annotations and the path to the saved
    dataset directory (or ``None`` on failure).
    """
    for hf_name in hf_names:
        try:
            # For layout‑rich datasets we use the specialised saver.
            if logical_name == "publaynet":
                count, path = _save_publaynet_split(hf_name, target_root, min_pages)
            else:
                # Generic fallback – just clone the repo (unlikely to be used for
                # layout‑rich data).
                from huggingface_hub import snapshot_download

                out_dir = target_root / logical_name
                out_dir.mkdir(parents=True, exist_ok=True)
                snapshot_download(
                    repo_id=hf_name,
                    repo_type="dataset",
                    local_dir=out_dir,
                    token=False,
                )
                count = count_pages_with_layout(out_dir)
                path = out_dir

            if count > 0:
                print(f"Successfully prepared '{hf_name}'. Pages with layout (estimated): {count}")
                return count, path
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
    - ``publaynet``: primary = PubLayNet, fallback = DocBank, with a
      minimum page‑count check.
    - ``docvqa`` (or any other name): a direct download via ``datasets``.
    """
    dataset_name = dataset_name.lower()
    if dataset_name == "publaynet":
        primary_hfs = ["layoutparser/publaynet"]
        fallback_hfs = ["layoutparser/docbank"]

        # 1. Try primary
        primary_count, primary_path = download_and_save(
            logical_name="publaynet",
            hf_names=primary_hfs,
            target_root=output_dir,
            min_pages=min_pages,
        )
        total_count = primary_count

        # 2. If insufficient, try fallback
        if total_count < min_pages:
            print(
                f"Primary dataset provided {total_count} pages, which is less than the required {min_pages}. "
                "Attempting fallback download..."
            )
            fallback_count, _ = download_and_save(
                logical_name="publaynet",
                hf_names=fallback_hfs,
                target_root=output_dir,
                min_pages=min_pages - total_count,
            )
            total_count += fallback_count

        print("\n=== Summary of layout‑annotation pages ===")
        print(f"  Primary (PubLayNet): {primary_count}")
        print(f"  Fallback (DocBank) added: {total_count - primary_count}")
        print(f"  TOTAL: {total_count}")

        if total_count < min_pages:
            raise RuntimeError(
                f"Insufficient total pages with layout annotations: {total_count} "
                f"(minimum required is {min_pages}). Pipeline aborting as per FR‑007."
            )
            # The exception propagates to ``main`` which turns it into a non‑zero exit.
        else:
            print(f"✅ Sufficient pages ({total_count} ≥ {min_pages}) – proceeding.")
    else:
        # Generic dataset – use ``datasets`` to fetch the split and store raw files.
        print(f"Downloading generic dataset '{dataset_name}' via 🤗 datasets...")
        try:
            ds = load_dataset(dataset_name, split="train")
            out_dir = output_dir / dataset_name
            out_dir.mkdir(parents=True, exist_ok=True)

            for idx, example in enumerate(tqdm(ds, desc="Saving generic dataset")):
                # Heuristic: if the example contains an image, store it; otherwise store the raw dict.
                if "image" in example and hasattr(example["image"], "save"):
                    img_path = out_dir / f"{idx:06d}.png"
                    example["image"].save(img_path)
                else:
                    json_path = out_dir / f"{idx:06d}.json"
                    with json_path.open("w", encoding="utf-8") as f:
                        json.dump(example, f)

            checksum_file = Path("artifacts") / "checksums" / "downloads.yaml"
            log_and_store_checksums(dataset_name, out_dir, checksum_file)
            print(f"✅ Dataset '{dataset_name}' downloaded successfully to {out_dir}.")
        except Exception as exc:
            raise RuntimeError(f"Failed to download generic dataset '{dataset_name}': {exc}") from exc


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
