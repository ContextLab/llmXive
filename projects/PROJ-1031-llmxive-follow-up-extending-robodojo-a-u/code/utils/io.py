"""
code/utils/io.py
-----------------
Utility module for loading the RoboDojo dataset with streaming and checksum validation.

The script can be executed as a module:
    python -m code.utils.io --test
    python -m code.utils.io --verify-checksums

The `--test` flag streams the first record from the 'real' split and
prints an identifier (task_id or id). Any failure to fetch the dataset
raises a RuntimeError, causing a non-zero exit status.

The `--verify-checksums` flag validates checksums for every record
(if a `checksum` field exists in the data).
"""
import argparse
import json
import hashlib
import sys
from typing import Generator, Dict, Any

from datasets import load_dataset
from llmxive_toolkit import get_logger

log = get_logger(__name__)

def _record_checksum(record: Dict[str, Any]) -> str:
    """Calculate SHA-256 checksum of a JSON-serialised record."""
    record_bytes = json.dumps(record, sort_keys=True).encode("utf-8")
    return hashlib.sha256(record_bytes).hexdigest()

def _validate_record(record: Dict[str, Any]) -> None:
    """
    Validate a single record.
    If the record contains a `checksum` field, it is compared against the
    computed SHA-256 hash of the record (excluding the checksum field).
    """
    expected = record.get("checksum")
    if expected is not None:
        record_copy = dict(record)
        record_copy.pop("checksum", None)
        computed = _record_checksum(record_copy)
        if computed != expected:
            raise ValueError(
                f"Checksum mismatch for record id={record.get('task_id', 'unknown')}: "
                f"expected {expected}, got {computed}"
            )

def _load_dataset() -> Any:
    """
    Load the RoboDojo dataset from HuggingFace with streaming enabled.
    """
    dataset_id = "robodojo"
    try:
        log.info("Loading dataset: %s", dataset_id)
        # trust_remote_code=True is often required for dataset loading scripts on HF
        return load_dataset(dataset_id, split="real", streaming=True, trust_remote_code=True)
    except Exception as exc:
        log.error("Failed to load dataset %s: %s", dataset_id, exc)
        raise RuntimeError(f"Unable to fetch dataset {dataset_id}") from exc

def stream_real_dataset() -> Generator[Dict[str, Any], None, None]:
    """
    Stream records from the RoboDojo 'real' split.
    """
    try:
        dataset = _load_dataset()
    except Exception as exc:
        log.error("Dataset loading failed: %s", exc)
        raise RuntimeError("Unable to fetch dataset") from exc

    for record in dataset:
        _validate_record(record)
        yield record

def test_stream() -> None:
    """
    Streams a single record, prints its identifier, and exits.
    """
    gen = stream_real_dataset()
    try:
        first_record = next(gen)
    except StopIteration:
        raise RuntimeError("Dataset is empty")
    
    task_identifier = (
        first_record.get("task_id")
        or first_record.get("id")
        or list(first_record.keys())[0]
    )
    log.info("Successfully streamed first record: %s", task_identifier)
    print(task_identifier)

def verify_checksums() -> None:
    """
    Verify checksums for the entire streamed dataset.
    """
    count = 0
    for _ in stream_real_dataset():
        count += 1
    log.info("Checksum verification completed for %d records.", count)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Utility for streaming the RoboDojo dataset."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Stream a single record and exit.",
    )
    parser.add_argument(
        "--verify-checksums",
        action="store_true",
        help="Validate checksums for the entire dataset.",
    )
    args = parser.parse_args(argv)

    try:
        if args.test:
            test_stream()
        elif args.verify_checksums:
            verify_checksums()
        else:
            count = 0
            for _ in stream_real_dataset():
                count += 1
            log.info("Streamed %d records from the dataset.", count)
    except Exception as exc:
        log.error("Dataset streaming failed: %s", exc)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
