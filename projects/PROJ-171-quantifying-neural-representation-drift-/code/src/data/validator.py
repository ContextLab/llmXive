"""
Input validator for the synthetic dataset.

The validator checks that each record contains the required variables
defined in the input schema and raises a ``RuntimeError`` with a clear
message if a variable is missing. It also validates the record against
the JSON‑Schema contract using ``jsonschema``.
"""

import json
from pathlib import Path

import jsonschema
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Load the JSON‑Schema once at import time
_SCHEMA_PATH = paths.code(
    "specs",
    "001-quantify-neural-representation-drift",
    "contracts",
    "input_schema.schema.yaml",
)
with _SCHEMA_PATH.open("r", encoding="utf-8") as f:
    _INPUT_SCHEMA = json.load(f)

_REQUIRED_FIELDS = ["subject_id", "session_id", "day_index", "spike_counts", "trial_success"]

def _raise_missing(field: str) -> None:
    """
    Helper to raise a RuntimeError with the required message format.
    """
    raise RuntimeError(f"Missing variable '{field}' at validation step")

def validate_record(record: dict) -> None:
    """
    Validate a single record.

    - Checks that all required top‑level keys are present.
    - Validates the record against the JSON‑Schema contract.

    Parameters
    ----------
    record : dict
        The record to validate.

    Raises
    ------
    RuntimeError
        If any required field is absent.
    jsonschema.ValidationError
        If the record does not conform to the schema.
    """
    for field in _REQUIRED_FIELDS:
        if field not in record:
            _raise_missing(field)

    # Schema validation (will raise jsonschema.ValidationError on failure)
    jsonschema.validate(instance=record, schema=_INPUT_SCHEMA)

def validate_file(jsonl_path: Path) -> list[dict]:
    """
    Validate all records in a JSON‑Lines file.

    Parameters
    ----------
    jsonl_path : Path
        Path to the ``*.jsonl`` file containing the records.

    Returns
    -------
    records : list[dict]
        The list of validated records (useful for downstream pipelines).

    Raises
    ------
    RuntimeError
        If any record is missing a required field.
    jsonschema.ValidationError
        If any record violates the schema.
    """
    records = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(
                    f"JSON decode error at line {line_number} in {jsonl_path}"
                ) from exc
            validate_record(rec)
            records.append(rec)
    log.info(f"Validated {len(records)} records from {jsonl_path}")
    return records
