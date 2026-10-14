"""
Dataset validation module (task T005).

Validates every JSONL entry in ``data/raw/`` against the dataset
contract ``specs/001-llmxive-follow-up-extending-eva-bench-a/contracts/dataset.schema.yaml``.

Behaviour (fail-fast, no silent fallback):
  * Exits with status 0 ONLY if at least one JSONL file was found and
    every record in every JSONL file conforms to the schema.
  * If any record fails validation, prints the offending record IDs
    (with the schema error) and exits with status 1.
  * If no JSONL files exist under the input directory (e.g. the T004
    download failed), exits with status 2 and a clear error message.
  * If the schema file cannot be located or parsed, exits with status 3.

Usage:
    python code/data/validate_dataset.py [--input data/raw] [--schema <path>]
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import jsonschema
import yaml

# Make sibling packages importable when run as `python code/data/validate_dataset.py`
_CODE_DIR = Path(__file__).resolve().parent.parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from config import PROJECT_ROOT, RAW_DATA_DIR, SPECS_DIR

DEFAULT_SCHEMA_NAME = "dataset.schema.yaml"

EXIT_OK = 0
EXIT_VALIDATION_FAILED = 1
EXIT_NO_DATA = 2
EXIT_SCHEMA_ERROR = 3


def find_schema_path(explicit: Optional[str] = None) -> Path:
    """Locate the dataset schema file.

    Resolution order:
      1. An explicitly provided path (CLI ``--schema``).
      2. ``<project>/specs/001-llmxive-follow-up-extending-eva-bench-a/contracts/dataset.schema.yaml``
      3. A recursive search for ``dataset.schema.yaml`` under ``specs/``.

    Raises:
        FileNotFoundError: if the schema cannot be located.
    """
    candidates: List[Path] = []
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = PROJECT_ROOT / p
        candidates.append(p)
    candidates.append(
        PROJECT_ROOT / "specs" / "001-llmxive-latency-study" / "contracts" / DEFAULT_SCHEMA_NAME
    )
    if SPECS_DIR.exists():
        candidates.extend(sorted(SPECS_DIR.rglob(DEFAULT_SCHEMA_NAME)))
    for cand in candidates:
        if cand.is_file():
            return cand
    raise FileNotFoundError(
        "Could not locate the dataset schema (dataset.schema.yaml). "
        f"Searched: {[str(c) for c in candidates]}"
    )


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the YAML schema. Raises on invalid YAML."""
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    if not isinstance(schema, dict):
        raise ValueError(f"Schema {schema_path} did not parse to a dict.")
    return schema


def iter_jsonl_files(raw_dir: Path) -> List[Path]:
    """Return all ``*.jsonl`` files under ``raw_dir`` (recursive, sorted)."""
    if not raw_dir.exists():
        return []
    return sorted(p for p in raw_dir.rglob("*.jsonl") if p.is_file())


def iter_records(jsonl_path: Path) -> Iterator[Tuple[int, Dict[str, Any]]]:
    """Yield ``(line_number, record)`` pairs from a JSONL file.

    Raises:
        json.JSONDecodeError: on a malformed line (fail-fast).
    """
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            yield lineno, json.loads(line)


def validate_dataset_dir(
    raw_dir: Path, schema: Dict[str, Any]
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Validate every JSONL record under ``raw_dir`` against ``schema``.

    Returns:
        (total_records, valid_count, failures) where each failure is a
        dict with keys ``file``, ``line``, ``record_id``, ``errors``.
    """
    validator = jsonschema.Draft7Validator(schema)
    total = 0
    valid = 0
    failures: List[Dict[str, Any]] = []

    for jsonl_path in iter_jsonl_files(raw_dir):
        for lineno, record in iter_records(jsonl_path):
            total += 1
            record_id = record.get("id") if isinstance(record, dict) else None
            record_id = record_id if record_id is not None else f"<line {lineno}>"
            errors = sorted(
                validator.iter_errors(record), key=lambda e: list(e.absolute_path)
            )
            if errors:
                failures.append(
                    {
                        "file": str(jsonl_path),
                        "line": lineno,
                        "record_id": record_id,
                        "errors": [
                            f"{list(e.absolute_path)}: {e.message}" for e in errors
                        ],
                    }
                )
            else:
                valid += 1
    return total, valid, failures


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate EVA-Bench JSONL dataset against the dataset schema contract."
    )
    parser.add_argument(
        "--input",
        default=str(RAW_DATA_DIR),
        help="Directory containing the raw JSONL files (default: data/raw).",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Path to dataset.schema.yaml (default: auto-detected under specs/).",
    )
    args = parser.parse_args(argv)

    raw_dir = Path(args.input)
    if not raw_dir.is_absolute():
        raw_dir = PROJECT_ROOT / raw_dir

    # 1. Locate and load the schema (fail-fast on any schema problem).
    try:
        schema_path = find_schema_path(args.schema)
        schema = load_schema(schema_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:
        print(f"SCHEMA ERROR: {e}", file=sys.stderr)
        return EXIT_SCHEMA_ERROR

    # 2. Fail loudly if no JSONL data exists (e.g. download failed).
    jsonl_files = iter_jsonl_files(raw_dir)
    if not jsonl_files:
        print(
            f"NO DATA: no *.jsonl files found under {raw_dir}. "
            "The dataset download (task T004) must succeed before "
            "validation can run. Aborting.",
            file=sys.stderr,
        )
        return EXIT_NO_DATA

    # 3. Validate every record.
    total, valid, failures = validate_dataset_dir(raw_dir, schema)

    print(
        f"Validated {total} record(s) across {len(jsonl_files)} JSONL file(s) "
        f"against {schema_path}: {valid} valid, {len(failures)} invalid."
    )

    if failures:
        print("\nOffending record IDs:")
        for failure in failures:
            print(f"  - id={failure['record_id']} ({failure['file']}:{failure['line']})")
            for err in failure["errors"]:
                print(f"      {err}")
        return EXIT_VALIDATION_FAILED

    print("Dataset validation PASSED: all records conform to the schema.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
