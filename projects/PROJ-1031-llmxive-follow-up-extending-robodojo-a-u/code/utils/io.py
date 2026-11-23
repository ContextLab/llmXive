"""
code/utils/io.py
-----------------
Utility module for loading the RoboDojo dataset with streaming and checksum validation.

The script can be executed as a module:
    python -m code.utils.io --test
    python -m code.utils.io --verify-checksums

The `--test` flag streams the first record from the RoboDojo dataset and
prints its identifier. Any failure to fetch the dataset raises a RuntimeError,
ensuring no silent fallback to synthetic data.

The `--verify-checksums` flag validates SHA-256 checksums for every record
if a `checksum` field is present in the data.
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
    """
    Calculate SHA-256 checksum of a JSON-serialised record.
    The 'checksum' field itself is excluded from the calculation.
    """
    record_copy = dict(record)
    record_copy.pop("checksum", None)
    record_bytes = json.dumps(record_copy, sort_keys=True).encode("utf-8")
    return hashlib.sha256(record_bytes).hexdigest()

def _validate_record(record: Dict[str, Any]) -> None:
    """
    Validate a single record against its provided checksum.
    If no 'checksum' field exists, the validation is a no-op.
    """
    expected = record.get("checksum")
    if expected is not None:
        computed = _record_checksum(record)
        if computed != expected:
            raise ValueError(
                f"Checksum mismatch for record id={record.get('task_id', 'unknown')}: "
                f"expected {expected}, got {computed}"
            )

def stream_dataset() -> Generator[Dict[str, Any], None, None]:
    """
    Stream records from the real RoboDojo dataset on HuggingFace.
    Per T004, uses the 'real' split with streaming enabled.
    """
    dataset_id = "robodojo"
    try:
        log.info("Loading real RoboDojo dataset: %s (streaming, split='real')", dataset_id)
        # Explicit requirement: datasets.load_dataset("robodojo", split="real", streaming=True)
        dataset = load_dataset(dataset_id, split="real", streaming=True)
    except Exception as exc:
        log.error("Failed to fetch the real RoboDojo dataset: %s", exc)
        # Fail loudly as per Core Constraint 9: no synthetic fallback.
        raise RuntimeError(f"Unable to fetch real dataset {dataset_id}") from exc

    for record in dataset:
        _validate_record(record)
        yield record

def test_stream() -> None:
    """
    Streams a single record, prints its identifier, and exits.
    Used for verification that the data source is reachable.
    """
    gen = stream_dataset()
    try:
        first_record = next(gen)
    except StopIteration:
        raise RuntimeError("RoboDojo dataset is empty")

    # Determine a human-readable identifier (task_id, id, or first key)
    task_identifier = (
        first_record.get("task_id")
        or first_record.get("id")
        or list(first_record.keys())[0]
    )
    log.info("Successfully streamed first record: %s", task_identifier)
    print(task_identifier)

def verify_checksums() -> None:
    """
    Iterate over the dataset to ensure streaming and checksums are valid.
    """
    count = 0
    for _ in stream_dataset():
        count += 1
    log.info("Checksum verification completed for %d records.", count)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Utility for streaming the real RoboDojo dataset."
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
            count = sum(1 for _ in stream_dataset())
            log.info("Streamed %d records from the RoboDojo dataset.", count)
    except Exception as exc:
        log.error("Dataset streaming failed: %s", exc)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())