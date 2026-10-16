"""Schema validators for the neural, text, and RSA data contracts.

Validators load a YAML (JSON-Schema-like) contract from disk and check
data files (CSV / JSON / JSONL) against it.  The three public entry
points are:

* ``validate_neural_data``  -> ``neural-data.schema.yaml``
* ``validate_text_data``    -> ``text-data.schema.yaml``
* ``validate_rsa_output``   -> ``rsa-output.schema.yaml``

plus a generic ``validate_data`` dispatcher and
``write_validation_report`` which persists a JSON report.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Project root (three levels up: code/utils/schema_validation.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Schema search locations, in priority order.
SCHEMA_DIRS = [
    PROJECT_ROOT / "contracts",
    PROJECT_ROOT / "specs" / "schemas",
]

SCHEMA_FILES = {
    "neural": "neural-data.schema.yaml",
    "text": "text-data.schema.yaml",
    "rsa": "rsa-output.schema.yaml",
}

_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


def _find_schema_path(schema_name: str) -> Optional[Path]:
    """Locate a schema file in any of the known schema directories."""
    for directory in SCHEMA_DIRS:
        candidate = directory / schema_name
        if candidate.exists():
            return candidate
    return None


def _load_schema(schema_name: str) -> Optional[Dict[str, Any]]:
    """Load a YAML schema file from the known schema directories."""
    schema_path = _find_schema_path(schema_name)
    if schema_path is None:
        logger.error(
            "Schema file not found in any of %s: %s",
            [str(d) for d in SCHEMA_DIRS],
            schema_name,
        )
        return None
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error("Failed to parse schema %s: %s", schema_name, e)
        return None


def _check_value_type(value: Any, expected_type: str) -> bool:
    """Return True if ``value`` matches the JSON-schema ``expected_type``."""
    expected_python_type = _TYPE_MAP.get(expected_type)
    if expected_python_type is None:
        return True  # unknown type keyword: nothing to check
    # bool is a subclass of int; keep integer checks strict
    if expected_type == "integer" and isinstance(value, bool):
        return False
    if expected_type == "number" and isinstance(value, bool):
        return False
    return isinstance(value, expected_python_type)


def _validate_against_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """Basic validation of a dict-like record against a schema.

    Checks ``required`` fields and ``properties`` type constraints.
    """
    if schema is None:
        return False

    if "required" in schema:
        if isinstance(data, dict):
            for field in schema["required"]:
                if field not in data:
                    logger.error("Missing required field in data: %s", field)
                    return False
        else:
            logger.error(
                "Data is not a dictionary but schema requires fields"
            )
            return False

    if "properties" in schema and isinstance(data, dict):
        for prop_name, prop_schema in schema.get("properties", {}).items():
            if not isinstance(prop_schema, dict):
                continue
            if prop_name in data:
                value = data[prop_name]
                expected_type = prop_schema.get("type")
                if expected_type and not _check_value_type(
                    value, expected_type
                ):
                    logger.error(
                        "Type mismatch for field '%s': expected %s, got %s",
                        prop_name,
                        expected_type,
                        type(value).__name__,
                    )
                    return False
                # enum constraint
                if "enum" in prop_schema and value not in prop_schema["enum"]:
                    logger.error(
                        "Value for field '%s' not in allowed enum: %r",
                        prop_name,
                        value,
                    )
                    return False
                # minimum / maximum for numbers
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    if "minimum" in prop_schema and value < prop_schema["minimum"]:
                        logger.error(
                            "Field '%s' below minimum %s: %r",
                            prop_name,
                            prop_schema["minimum"],
                            value,
                        )
                        return False
                    if "maximum" in prop_schema and value > prop_schema["maximum"]:
                        logger.error(
                            "Field '%s' above maximum %s: %r",
                            prop_name,
                            prop_schema["maximum"],
                            value,
                        )
                        return False
    return True


def _validate_csv(path_obj: Path, schema: Dict[str, Any]) -> bool:
    """Validate a CSV file: required columns plus per-row type checks."""
    with open(path_obj, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        if not headers:
            logger.error("CSV file is empty or has no headers: %s", path_obj)
            return False

        required_fields = schema.get("required", [])
        if required_fields:
            missing = set(required_fields) - set(headers)
            if missing:
                logger.error(
                    "CSV missing required columns: %s", sorted(missing)
                )
                return False

        properties = schema.get("properties", {})
        numeric_fields = [
            name
            for name, prop in properties.items()
            if isinstance(prop, dict)
            and prop.get("type") in ("number", "integer")
            and name in headers
        ]

        n_rows = 0
        for row in reader:
            n_rows += 1
            for field in numeric_fields:
                raw = row.get(field)
                if raw is None or raw == "":
                    continue
                try:
                    value = float(raw)
                except ValueError:
                    logger.error(
                        "Column '%s' contains non-numeric data %r at row %d",
                        field,
                        raw,
                        n_rows + 1,
                    )
                    return False
                if isinstance(prop := properties.get(field), dict):
                    if "minimum" in prop and value < prop["minimum"]:
                        logger.error(
                            "Column '%s' below minimum at row %d",
                            field,
                            n_rows + 1,
                        )
                        return False
                    if "maximum" in prop and value > prop["maximum"]:
                        logger.error(
                            "Column '%s' above maximum at row %d",
                            field,
                            n_rows + 1,
                        )
                        return False
        if n_rows == 0:
            logger.error("CSV file has headers but no data rows: %s", path_obj)
            return False
    return True


def _validate_jsonl(path_obj: Path, schema: Dict[str, Any]) -> bool:
    """Validate every record of a JSONL file against the schema."""
    with open(path_obj, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSONL line %d: %s", i, e)
                return False
            if not _validate_against_schema(record, schema):
                logger.error("Invalid JSONL record at line %d", i)
                return False
    return True


def _validate_file(data_path: str, schema: Dict[str, Any]) -> bool:
    """Dispatch validation by file extension."""
    path_obj = Path(data_path)
    if not path_obj.exists():
        logger.error("Data file not found: %s", data_path)
        return False

    suffix = path_obj.suffix.lower()
    try:
        if suffix == ".csv":
            return _validate_csv(path_obj, schema)
        if suffix == ".jsonl":
            return _validate_jsonl(path_obj, schema)
        if suffix == ".json":
            with open(path_obj, "r", encoding="utf-8") as f:
                data_obj = json.load(f)
            if isinstance(data_obj, list):
                return all(
                    _validate_against_schema(rec, schema) for rec in data_obj
                )
            return _validate_against_schema(data_obj, schema)
        logger.error("Unsupported file format: %s", suffix)
        return False
    except Exception as e:  # noqa: BLE001 - report and fail loudly
        logger.error("Error reading data file %s: %s", data_path, e)
        return False


def _validate_contract(data_path: Optional[str], schema_name: str) -> bool:
    """Shared implementation for the three contract validators."""
    schema = _load_schema(schema_name)
    if not schema:
        return False
    if not data_path:
        logger.warning(
            "Validation called without a data path; skipping content "
            "validation (schema %s loaded successfully).",
            schema_name,
        )
        return True
    return _validate_file(data_path, schema)


def validate_neural_data(data_path: Optional[str] = None) -> bool:
    """Validate neural data (ROI timecourses / event averages) against
    ``neural-data.schema.yaml``.

    Args:
        data_path: Path to the data file (CSV, JSON, or JSONL).

    Returns:
        True if valid, False otherwise.
    """
    return _validate_contract(data_path, SCHEMA_FILES["neural"])


def validate_text_data(data_path: Optional[str] = None) -> bool:
    """Validate text data (ROCStories sample / transcripts) against
    ``text-data.schema.yaml``.

    Args:
        data_path: Path to the data file (JSONL or JSON).

    Returns:
        True if valid, False otherwise.
    """
    return _validate_contract(data_path, SCHEMA_FILES["text"])


def validate_rsa_output(data_path: Optional[str] = None) -> bool:
    """Validate RSA output against ``rsa-output.schema.yaml``.

    Args:
        data_path: Path to the RSA output file (CSV or JSON).

    Returns:
        True if valid, False otherwise.
    """
    return _validate_contract(data_path, SCHEMA_FILES["rsa"])


def validate_data(
    contract: str, data_path: Optional[str] = None
) -> Dict[str, Any]:
    """Validate ``data_path`` against the named contract.

    Args:
        contract: One of ``"neural"``, ``"text"``, ``"rsa"``.
        data_path: Path to the data file.

    Returns:
        A report dict with keys ``contract``, ``data_path``, ``valid``,
        and ``schema_file``.

    Raises:
        ValueError: If the contract name is unknown.
    """
    if contract not in SCHEMA_FILES:
        raise ValueError(
            f"Unknown contract {contract!r}; expected one of "
            f"{sorted(SCHEMA_FILES)}"
        )
    validators = {
        "neural": validate_neural_data,
        "text": validate_text_data,
        "rsa": validate_rsa_output,
    }
    valid = validators[contract](data_path)
    return {
        "contract": contract,
        "data_path": str(data_path) if data_path else None,
        "schema_file": SCHEMA_FILES[contract],
        "valid": valid,
    }


def write_validation_report(
    reports: List[Dict[str, Any]], output_path: str
) -> Path:
    """Persist a list of validation reports as a JSON file.

    Args:
        reports: List of report dicts (e.g. from ``validate_data``).
        output_path: Destination JSON path.

    Returns:
        The path written.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "all_valid": all(r.get("valid", False) for r in reports),
        "reports": reports,
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return out


def main(argv: Optional[List[str]] = None) -> int:
    """CLI: validate a file against a contract.

    Usage: python -m utils.schema_validation <contract> <data_path>
    """
    import sys

    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(
            "Usage: python -m utils.schema_validation "
            "<neural|text|rsa> <data_path>"
        )
        return 2
    contract, data_path = args
    try:
        report = validate_data(contract, data_path)
    except ValueError as e:
        print(str(e))
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
