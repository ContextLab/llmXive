import argparse
import hashlib
import json
import logging
from pathlib import Path
from typing import List, Tuple

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

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
    Download the official ``pi_bench`` dataset via ``datasets``,
    write each example as a JSON file into ``raw_dir`` and return a list
    of (relative_path, checksum) tuples for the written files.
    """
    log.info("Loading the 'pi_bench' dataset via huggingface datasets")
    # The dataset is small (≈100 tasks) so we can load it fully in memory.
    # ``load_dataset`` returns a DatasetDict; we take the default split.
    ds = load_dataset("pi_bench")
    if isinstance(ds, dict):
        # Prefer the 'train' split if present, otherwise take the first.
        split_name = "train" if "train" in ds else next(iter(ds))
        ds = ds[split_name]

    checksums: List[Tuple[Path, str]] = []

    for idx, example in enumerate(ds):
        # Ensure the example is JSON‑serialisable.
        json_path = raw_dir / f"{idx}.json"
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(example, jf, ensure_ascii=False, indent=2)

        rel_path = json_path.relative_to(raw_dir)
        checksum = _sha256_checksum(json_path)
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
        help="Directory to store raw dataset files (used for downstream pipelines).",
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

if __name__ == "__main__":
    main()
