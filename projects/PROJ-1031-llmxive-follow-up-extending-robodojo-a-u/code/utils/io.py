"""
code/utils/io.py
-----------------
Utility module for loading the RoboDojo dataset with streaming and basic
checksum validation.

The script can be executed as a module:
    python -m code.utils.io --test

The ``--test`` flag streams the first record from the real‑world split
and validates its checksum (if a ``checksum`` field is present).  Any
failure to fetch the dataset or a checksum mismatch raises an exception,
causing a non‑zero exit status as required by the verification step.
"""
import argparse
import json
import hashlib
import sys
from typing import Generator, Dict, Any

from datasets import load_dataset
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _record_checksum(record: Dict[str, Any]) -> str:
    """Calculate SHA‑256 checksum of a JSON‑serialised record."""
    # Ensure deterministic ordering for reproducible hash
    record_bytes = json.dumps(record, sort_keys=True).encode("utf-8")
    return hashlib.sha256(record_bytes).hexdigest()

def _validate_record(record: Dict[str, Any]) -> None:
    """
    Validate a single record.

    If the record contains a ``checksum`` field, it is compared against the
    computed SHA‑256 hash of the whole record (excluding the ``checksum``
    field itself).  A mismatch raises ``ValueError``.
    """
    expected = record.get("checksum")
    if expected is not None:
        # Compute checksum without the stored ``checksum`` to avoid circularity
        record_copy = dict(record)
        record_copy.pop("checksum", None)
        computed = _record_checksum(record_copy)
        if computed != expected:
            raise ValueError(
                f"Checksum mismatch for record id={record.get('task_id', 'unknown')}: "
                f"expected {expected}, got {computed}"
            )

def stream_real_dataset() -> Generator[Dict[str, Any], None, None]:
    """
    Stream the ``real`` split of the RoboDojo dataset.

    Yields:
        Dictionaries representing individual task records.

    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    try:
        # The ``robodojo`` dataset is hosted on HuggingFace Hub.
        # ``streaming=True`` ensures we never load the full dataset into RAM.
        dataset = load_dataset("robodojo", split="real", streaming=True)
    except Exception as exc:
        log.error("Failed to load RoboDojo dataset: %s", exc)
        raise RuntimeError("Unable to fetch RoboDojo dataset") from exc

    for record in dataset:
        # Basic validation – raise on checksum mismatch if the field exists.
        _validate_record(record)
        yield record

def test_stream() -> None:
    """
    Test helper used by the ``--test`` CLI flag.

    Streams a single record, prints its ``task_id`` (or ``id``) to stdout,
    and exits with status 0 on success.  Any exception propagates and will
    cause a non‑zero exit code.
    """
    gen = stream_real_dataset()
    first_record = next(gen)  # Will raise StopIteration if dataset is empty
    task_identifier = first_record.get("task_id") or first_record.get("id")
    log.info("Successfully streamed first RoboDojo record: %s", task_identifier)
    print(task_identifier)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Utility for streaming the RoboDojo real‑world dataset."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Stream a single record and exit (used for verification).",
    )
    args = parser.parse_args(argv)

    try:
        if args.test:
            test_stream()
        else:
            # If no flag is provided, simply iterate through the dataset
            # to ensure the streaming pipeline works without errors.
            count = 0
            for _ in stream_real_dataset():
                count += 1
            log.info("Streamed %d records from the RoboDojo real split.", count)
    except Exception as exc:  # pragma: no cover – any exception is a failure
        log.error("Dataset streaming failed: %s", exc)
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
