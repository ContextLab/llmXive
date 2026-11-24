"""
Data download & checksum script for T003.

Downloads the BigBench Hard and Ethics datasets using the HuggingFace `datasets`
library with streaming enabled, shards the data into JSONL files, computes a SHA‑256
checksum for each shard, and writes a manifest file `data/raw/checksums.json`.

The script aborts loudly if any download or write operation fails.
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict

import datasets
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Configuration
DATASETS_TO_DOWNLOAD = [
    {"name": "bigbench/hard", "split": "train"},
    {"name": "bigbench/ethics", "split": "train"},
]
SHARD_SIZE = 1000  # Number of examples per shard JSONL file


def _stream_and_shard(
    dataset_name: str, split: str, output_dir: Path
) -> List[Dict[str, str]]:
    """
    Streams a HuggingFace dataset, writes it to shard files, and returns a list
    of checksum entries for each shard.

    Parameters
    ----------
    dataset_name: str
        The HuggingFace identifier (e.g., "bigbench/hard").
    split: str
        The split to load (usually "train").
    output_dir: Path
        Directory where shard files will be written.

    Returns
    -------
    List[Dict[str, str]]
        A list of checksum dictionaries with keys:
        - dataset: the dataset identifier
        - shard_index: integer index of the shard
        - filename: relative filename of the shard
        - checksum: SHA‑256 hex digest of the shard file
    """
    log.info(f"Streaming dataset '{dataset_name}' (split='{split}')...")
    try:
        stream = datasets.load_dataset(
            dataset_name, split=split, streaming=True
        )
    except Exception as e:
        log.error(f"Failed to load dataset {dataset_name}: {e}")
        raise

    output_dir.mkdir(parents=True, exist_ok=True)

    shard_idx = 0
    buffer: List[Dict] = []
    checksums: List[Dict[str, str]] = []

    for idx, example in enumerate(stream):
        # Normalise fields to a common schema
        normalized = {
            "prompt_text": example.get("question") or example.get("prompt") or example.get("instruction"),
            "rationale_text": example.get("answer") or example.get("response") or example.get("chosen"),
            "source": dataset_name,
        }
        buffer.append(normalized)

        if len(buffer) >= SHARD_SIZE:
            shard_path = output_dir / f"{dataset_name.replace('/', '_')}_shard_{shard_idx}.jsonl"
            _write_shard(buffer, shard_path)
            checksum = _file_sha256(shard_path)
            checksums.append(
                {
                    "dataset": dataset_name,
                    "shard_index": shard_idx,
                    "filename": str(shard_path.relative_to(paths.root)),
                    "checksum": checksum,
                }
            )
            log.info(f"Wrote shard {shard_idx} ({len(buffer)} records) – checksum {checksum}")
            buffer.clear()
            shard_idx += 1

    # Write any remaining records as the final shard
    if buffer:
        shard_path = output_dir / f"{dataset_name.replace('/', '_')}_shard_{shard_idx}.jsonl"
        _write_shard(buffer, shard_path)
        checksum = _file_sha256(shard_path)
        checksums.append(
            {
                "dataset": dataset_name,
                "shard_index": shard_idx,
                "filename": str(shard_path.relative_to(paths.root)),
                "checksum": checksum,
            }
        )
        log.info(f"Wrote final shard {shard_idx} ({len(buffer)} records) – checksum {checksum}")

    return checksums


def _write_shard(records: List[Dict], shard_path: Path) -> None:
    """Write a list of dict records to a JSONL file."""
    try:
        with shard_path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        log.error(f"Failed to write shard file {shard_path}: {e}")
        raise


def _file_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    sha256 = hashlib.sha256()
    try:
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
    except Exception as e:
        log.error(f"Failed to compute checksum for {file_path}: {e}")
        raise
    return sha256.hexdigest()


def main() -> None:
    """
    Entry point for the data‑download step.

    - Streams each required dataset.
    - Writes shard files under `data/raw/`.
    - Generates `data/raw/checksums.json` containing a list of checksum entries.
    """
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    all_checksums: List[Dict[str, str]] = []

    for spec in DATASETS_TO_DOWNLOAD:
        dataset_name = spec["name"]
        split = spec["split"]
        try:
            checksums = _stream_and_shard(dataset_name, split, raw_dir)
            all_checksums.extend(checksums)
        except Exception as e:
            log.error(f"Aborting due to failure while processing {dataset_name}: {e}")
            raise  # Propagate to abort the whole pipeline

    # Write the manifest file
    checksums_path = raw_dir / "checksums.json"
    try:
        with checksums_path.open("w", encoding="utf-8") as f:
            json.dump(all_checksums, f, indent=2, ensure_ascii=False)
        log.info(f"Checksums manifest written to {checksums_path}")
    except Exception as e:
        log.error(f"Failed to write checksums manifest: {e}")
        raise


if __name__ == "__main__":
    main()
