import sys
import os
import argparse
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import List, Tuple, Optional

try:
    from datasets import load_dataset, DatasetDict
except ImportError as e:
    raise ImportError(
        "The 'datasets' library is required. Ensure requirements.txt includes 'datasets' and 'pyarrow'."
    ) from e

from llmxive_toolkit import paths, get_logger

# Initialize logger
log = get_logger(__name__)

def _sha256_checksum(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_checksums(files: List[Tuple[Path, str]], out_path: Path) -> None:
    """Write a manifest of SHA‑256 checksums."""
    with out_path.open("w", encoding="utf-8") as f:
        for rel_path, checksum in files:
            f.write(f"{checksum}  {rel_path}\n")
    log.info(f"Checksum manifest written to {out_path}")

def _download_pi_bench(raw_dir: Path, max_examples: Optional[int] = None) -> List[Tuple[Path, str]]:
    """
    Stream the official pi-Bench dataset into raw_dir as JSON files.
    Tries multiple known identifiers to avoid 'Dataset scripts no longer supported' errors.
    """
    # Try the requested ID first, then the author's namespace as a fallback
    dataset_ids = ["pi_bench", "haoran-zhang/pi-bench"]
    
    ds = None
    last_exception = None

    for dataset_id in dataset_ids:
        attempts = 3
        for attempt in range(1, attempts + 1):
            try:
                log.info(f"Attempt {attempt} to load dataset '{dataset_id}' (streaming=True, trust_remote_code=True)")
                # trust_remote_code=True is essential for datasets using loading scripts
                ds = load_dataset(dataset_id, streaming=True, trust_remote_code=True)
                
                # If it's a DatasetDict, take the first available split (usually 'train')
                if isinstance(ds, DatasetDict) or hasattr(ds, 'keys'):
                    split = next(iter(ds.keys()))
                    ds = ds[split]
                
                # Test if the stream is actually working by trying to get one item
                next(iter(ds))
                log.info(f"Successfully connected to dataset '{dataset_id}'")
                break
            except Exception as exc:
                last_exception = exc
                log.warning(f"Failed to load {dataset_id} on attempt {attempt}: {exc}")
                if attempt < attempts:
                    time.sleep(2)
        
        if ds is not None:
            break

    if ds is None:
        raise RuntimeError(
            f"Unable to load pi-Bench dataset using tried IDs {dataset_ids}. "
            f"Last error: {last_exception}"
        ) from last_exception

    checksums: List[Tuple[Path, str]] = []
    
    # Iterate through the streaming dataset and save each example as a separate JSON file.
    for idx, example in enumerate(ds):
        if max_examples is not None and idx >= max_examples:
            break
        
        # Use task_id or index for filename
        task_id = example.get("task_id") or example.get("id") or f"task_{idx:05d}"
        safe_id = "".join(c if c.isalnum() or c in "._-" else "_" for c in str(task_id))
        json_path = raw_dir / f"{safe_id}.json"
        
        with json_path.open("w", encoding="utf-8") as jf:
            json.dump(example, jf, ensure_ascii=False, indent=2)

        rel_path = json_path.relative_to(raw_dir)
        checksum = _sha256_checksum(json_path)
        checksums.append((rel_path, checksum))

        if (idx + 1) % 10 == 0:
            log.debug(f"Written {idx + 1} JSON files")

    log.info(f"Finished writing {len(checksums)} JSON files to {raw_dir}")
    return checksums

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download the official pi-Bench dataset and verify checksums."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(paths.data("raw")),
        help="Directory to store raw dataset files.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=None,
        help="Maximum number of examples to download. Set to a number for faster CI.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    try:
        checksums = _download_pi_bench(raw_dir, max_examples=args.max_examples)
    except Exception as exc:
        log.error(f"Failed to download or process the pi-Bench dataset: {exc}")
        raise

    # Write basic manifest
    manifest_path = raw_dir / "download_manifest.txt"
    with manifest_path.open("w", encoding="utf-8") as mf:
        mf.write("pi_bench dataset downloaded via HuggingFace 'datasets' library\n")
    
    # Write checksum manifest
    checksum_path = raw_dir / "checksums.txt"
    _write_checksums(checksums, checksum_path)

    log.info("pi-Bench download and verification completed successfully.")
    print("✅ π‑Bench download verified")

if __name__ == "__main__":
    main()
