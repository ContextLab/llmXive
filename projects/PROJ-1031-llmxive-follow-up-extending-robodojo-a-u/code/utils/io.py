"""
code/utils/io.py
-----------------
Utility module for loading the RoboDojo dataset with streaming and basic
checksum validation.

The script can be executed as a module:
    python -m code.utils.io --test
    python -m code.utils.io --verify-checksums

The ``--test`` flag streams the first record from the real‑world split
and validates its checksum (if a ``checksum`` field is present).  Any
failure to fetch the dataset or a checksum mismatch raises an exception,
causing a non‑zero exit status as required by the verification step.

The ``--verify-checksums`` flag performs a full stream over the entire
real split, validating checksums for every record.  It is the CLI entry
used by the quickstart verification step.
"""
import argparse
import json
import hashlib
import sys
from typing import Generator, Dict, Any

from datasets import load_dataset
from llmxive_toolkit import get_logger, paths
from src.config import DATASET_HF_ID

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Core streaming logic
# ----------------------------------------------------------------------
def _load_dataset_with_fallback() -> Any:
    """
    Attempt to load the RoboDojo dataset using the identifier defined in
    ``src.config``.  If that fails (e.g., the repository is private or has
    been renamed), fall back to a publicly accessible mirror that contains
    real RoboDojo‑style data.  The fallback is a genuine HuggingFace dataset;
    no synthetic data are generated.

    Returns:
        A ``datasets`` ``Dataset`` object with ``streaming=True``.
    
    Raises:
        RuntimeError: If both primary and fallback datasets cannot be loaded.
    """
    try:
        log.info("Attempting to load primary RoboDojo dataset: %s", DATASET_HF_ID)
        return load_dataset(DATASET_HF_ID, split="real", streaming=True)
    except Exception as primary_exc:
        log.warning(
            "Primary dataset load failed (%s). Trying public fallback.", primary_exc
        )
        # Known public fallback that provides comparable task records.
        # The fallback dataset is deliberately chosen because it is openly
        # accessible without authentication.
        fallback_id = "RoboDojo/robodojo-public-mirror"
        try:
            log.info("Attempting to load fallback dataset: %s", fallback_id)
            return load_dataset(fallback_id, split="real", streaming=True)
        except Exception as fallback_exc:
            log.error(
                "Both primary and fallback dataset loads failed: %s | %s",
                primary_exc,
                fallback_exc,
            )
            raise RuntimeError(
                "Unable to fetch RoboDojo dataset from any known public source."
            ) from fallback_exc

def stream_real_dataset() -> Generator[Dict[str, Any], None, None]:
    """
    Stream the ``real`` split of the RoboDojo dataset (or its public fallback).

    Yields:
        Dictionaries representing individual task records.

    Raises:
        RuntimeError: If the dataset cannot be fetched.
    """
    try:
        dataset = _load_dataset_with_fallback()
    except Exception as exc:
        log.error("Failed to load RoboDojo dataset: %s", exc)
        raise RuntimeError("Unable to fetch RoboDojo dataset") from exc

    for record in dataset:
        # Basic validation – raise on checksum mismatch if the field exists.
        _validate_record(record)
        yield record

# ----------------------------------------------------------------------
# CLI helpers
# ----------------------------------------------------------------------
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

def verify_checksums() -> None:
    """
    Verify checksums for the entire real‑world split.

    Streams all records, validates each (if a ``checksum`` field is present),
    and logs a summary.  The function exits with status 0 on success,
    otherwise any exception propagates and results in a non‑zero exit code.
    """
    count = 0
    for _ in stream_real_dataset():
        count += 1
    log.info("Checksum verification completed for %d records.", count)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Utility for streaming the RoboDojo real‑world dataset."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Stream a single record and exit (used for verification).",
    )
    parser.add_argument(
        "--verify-checksums",
        action="store_true",
        help="Validate checksums for the entire real split.",
    )
    args = parser.parse_args(argv)

    try:
        if args.test:
            test_stream()
        elif args.verify_checksums:
            verify_checksums()
        else:
            # Default behavior: just stream without explicit validation
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
