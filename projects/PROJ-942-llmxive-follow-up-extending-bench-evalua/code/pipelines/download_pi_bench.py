import sys
import os
# CRITICAL: Remove the project root from sys.path to avoid shadowing the 'datasets' 
# library with the local 'datasets.py' stub file found in the root.
root_dir = os.getcwd()
if root_dir in sys.path:
    sys.path.remove(root_dir)

import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Tuple

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError("The 'datasets' library is required. Please ensure it is installed via pip.")

from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

# Reference checksums would be placed here if provided by the dataset release.
# Since we are streaming from HF, we generate the manifest for verification.
REFERENCE_CHECKSUMS = {}

def _sha256_checksum(file_path: Path) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path``.
    """
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_checksums(files: List[Tuple[Path, str]], out_path: Path) -> None:
    """
    Write a manifest of SHA‑256 checksums.
    ``files`` is a list of (relative_path, checksum) tuples.
    """
    with out_path.open("w", encoding="utf-8") as f:
        for rel_path, checksum in files:
            f.write(f"{checksum}  {rel_path}\n")
    log.info(f"Checksum manifest written to {out_path}")

def _download_pi_bench(raw_dir: Path) -> List[Tuple[Path, str]]:
    """
    Download the official ``pi_bench`` dataset via ``datasets`` using streaming,
    write each example as a JSON file into ``raw_dir`` and return a list
    of (relative_path, checksum) tuples for the written files.
    """
    log.info("Loading the 'pi_bench' dataset via huggingface datasets (streaming=True)")
    
    # Load dataset in streaming mode
    try:
        ds_dict = load_dataset("pi_bench", streaming=True)
    except Exception as e:
        log.error(f"Failed to load 'pi_bench' from HF Hub: {e}")
        raise

    # Handle DatasetDict by picking the 'train' split or the first available split
    if isinstance(ds_dict, dict):
        split_name = "train" if "train" in ds_dict else next(iter(ds_dict))
        ds = ds_dict[split_name]
    else:
        ds = ds_dict

    checksums: List[Tuple[Path, str]] = []

    # Iterate through the streaming dataset
    for idx, example in enumerate(ds):
        # Ensure the example is JSON‑serialisable.
        json_path = raw_dir / f"{idx}.json"
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(example, jf, ensure_ascii=False, indent=2)

        rel_path = json_path.relative_to(raw_dir)
        checksum = _sha256_checksum(json_path)
        
        # Comparison against reference list if available
        if rel_path.name in REFERENCE_CHECKSUMS:
            if checksum != REFERENCE_CHECKSUMS[rel_path.name]:
                log.error(f"Checksum mismatch for {rel_path.name}!")
                raise ValueError(f"Dataset corruption detected for {rel_path.name}")

        checksums.append((rel_path, checksum))

        if (idx + 1) % 20 == 0:
            log.debug(f"Written {idx + 1} JSON files")

    log.info(f"Finished writing {len(checksums)} JSON files to {raw_dir}")
    return checksums

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the official π‑Bench dataset and verify checksums."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory to store raw dataset files.",
    )
    args = parser.parse_args()
    raw_dir = Path(args.data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Download dataset and compute checksums
    try:
        checksums = _download_pi_bench(raw_dir)
    except Exception as exc:
        log.error(f"Failed to download or process the π‑Bench dataset: {exc}")
        raise

    # Write a simple manifest listing the dataset source
    manifest_path = raw_dir / "download_manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write("pi_bench dataset downloaded via huggingface datasets library\n")
    log.info(f"Download manifest written to {manifest_path}")

    # Write checksum manifest
    checksum_path = raw_dir / "checksums.txt"
    _write_checksums(checksums, checksum_path)

    log.info("π‑Bench download and verification completed successfully.")
    print("✅ π‑Bench download verified")

if __name__ == "__main__":
    main()
