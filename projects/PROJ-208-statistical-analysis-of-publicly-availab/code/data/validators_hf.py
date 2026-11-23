"""
validators_hf.py
-----------------

Schema validator for the HuggingFace dataset ``akhousker/github-issues``.
It ensures that each record contains the required fields with the
expected data types:

* ``created_at``      – ISO‑8601 timestamp (string)
* ``closed_at``       – ISO‑8601 timestamp (string)
* ``labels``          – list of strings (may be empty)
* ``assignee``        – string (GitHub login) or ``None``
* ``comments_count``  – integer (>= 0)

The validator is deliberately strict: missing fields or type mismatches
raise a ``ValueError`` with a clear message.  This behaviour is required
by functional requirement **FR‑001** – the dataset must be validated
before downstream processing.

The module exports two public helpers:

* ``validate_record(record: dict) -> None``
* ``validate_dataset(dataset) -> None``

``validate_dataset`` accepts either a ``datasets.Dataset`` object or any
iterable of mapping objects (e.g. a list of dicts).  It iterates over the
records and calls ``validate_record`` for each entry.  If any record is
invalid, the function raises the first encountered ``ValueError``; this
makes the failure loud and prevents silent fallback to synthetic data,
satisfying the execution‑gate policy.

Example usage::

    from datasets import load_dataset
    from code.data.validators_hf import validate_dataset

    ds = load_dataset("akhousker/github-issues", split="train")
    validate_dataset(ds)   # raises on the first schema violation
"""

from typing import Any, Iterable, Mapping

# The expected field names – kept as a constant for easy reuse.
REQUIRED_FIELDS = {
    "created_at": str,
    "closed_at": str,
    "labels": list,
    "assignee": (str, type(None)),
    "comments_count": int,
}

def _type_name(expected: Any) -> str:
    """Return a human‑readable name for a type or a tuple of types."""
    if isinstance(expected, tuple):
        return " or ".join(t.__name__ for t in expected)
    return expected.__name__

def validate_record(record: Mapping[str, Any]) -> None:
    """
    Validate a single record from the HuggingFace dataset.

    Parameters
    ----------
    record: Mapping[str, Any]
        The dataset row to validate.

    Raises
    ------
    ValueError
        If a required field is missing or its type does not match the
        specification.
    """
    # Ensure all required fields exist.
    missing = [field for field in REQUIRED_FIELDS if field not in record]
    if missing:
        raise ValueError(
            f"Record is missing required fields: {', '.join(missing)}"
        )

    # Validate each field's type.
    for field, expected_type in REQUIRED_FIELDS.items():
        value = record[field]
        if not isinstance(value, expected_type):
            raise ValueError(
                f"Field '{field}' has invalid type. Expected {_type_name(expected_type)}, "
                f"got {type(value).__name__}"
            )

    # Additional sanity checks for specific fields.
    if isinstance(record["labels"], list):
        if not all(isinstance(label, str) for label in record["labels"]):
            raise ValueError(
                "All elements in 'labels' must be strings."
            )

    if isinstance(record["comments_count"], int):
        if record["comments_count"] < 0:
            raise ValueError(
                "'comments_count' must be a non‑negative integer."
            )

    # ``created_at`` and ``closed_at`` are expected to be ISO‑8601 strings.
    # We perform a lightweight check without full parsing to keep the
    # validator fast for streaming datasets.
    for ts_field in ("created_at", "closed_at"):
        ts_value = record[ts_field]
        if not isinstance(ts_value, str) or "T" not in ts_value:
            raise ValueError(
                f"Field '{ts_field}' does not appear to be an ISO‑8601 timestamp: {ts_value!r}"
            )

def validate_dataset(dataset: Iterable[Mapping[str, Any]]) -> None:
    """
    Validate an entire HuggingFace dataset.

    The function iterates over ``dataset`` (which can be a
    ``datasets.Dataset`` or any iterable of ``dict``‑like objects) and
    validates each record using :func:`validate_record`.  The first
    validation error encountered aborts the iteration and is re‑raised.

    Parameters
    ----------
    dataset: Iterable[Mapping[str, Any]]
        The dataset to validate.

    Raises
    ------
    ValueError
        Propagated from :func:`validate_record` when a record is invalid.
    """
    for idx, record in enumerate(dataset):
        try:
            validate_record(record)
        except ValueError as exc:
            # Include the index to aid debugging of large streaming datasets.
            raise ValueError(f"Validation error at record {idx}: {exc}") from exc

__all__ = ["validate_record", "validate_dataset"]