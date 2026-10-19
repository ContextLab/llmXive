"""
Contract‑validation test suite.

Scans the ``data`` directory for JSON and CSV artefacts and validates each
file against the appropriate JSON‑Schema (when a matching schema can be
inferred).  CSV files are merely checked for parsability.

The test is deliberately permissive – it only asserts that files which have
a known schema validate successfully.  Files without a recognised schema
are ignored, which means the suite will still pass even when the project
has not yet generated every artefact.
"""

import csv
import json
from pathlib import Path

import pytest

from orchestrator.contract_validator import validate_schema, load_schema_from_yaml

# Mapping from a filename pattern to the schema file name (located in ``contracts/``)
SCHEMA_MAP = {
    "physical_node": "physical-node.schema.yaml",
    "dropout_events": "dropout-event.schema.yaml",
    "execution_run": "execution-run.schema.yaml",
    "regression_model": "regression-model.schema.yaml",
}

def _discover_data_files() -> list[Path]:
    """Return a list of JSON and CSV files under the ``data`` folder."""
    base = Path("data")
    return [p for p in base.rglob("*") if p.suffix.lower() in {".json", ".csv"}]

@pytest.mark.parametrize("data_path", _discover_data_files())
def test_data_file_schema_validation(data_path: Path):
    """Validate JSON files against a known schema; ensure CSV files are readable."""
    if data_path.suffix.lower() == ".json":
        # Load JSON content
        try:
            content = json.loads(data_path.read_text())
        except json.JSONDecodeError as exc:
            pytest.fail(f"Invalid JSON in {data_path}: {exc}")

        # Determine which schema (if any) applies
        schema_file = None
        for pattern, schema_name in SCHEMA_MAP.items():
            if pattern in data_path.stem:
                schema_file = schema_name
                break

        if schema_file is None:
            # No known schema – the test simply ensures the file is well‑formed JSON.
            return

        # Load the schema and validate
        schema_path = Path("contracts") / schema_file
        if not schema_path.is_file():
            pytest.fail(f"Schema file {schema_path} not found for {data_path}")

        # ``validate_schema`` expects the *name* of the schema file.
        # It internally loads the schema from ``contracts/``.
        assert validate_schema(content, schema_file), f"{data_path} failed schema validation"

    else:
        # CSV validation – ensure the file can be opened and has at least a header row.
        try:
            with data_path.open(newline="") as f:
                reader = csv.reader(f)
                rows = list(reader)
        except Exception as exc:  # pragma: no cover – defensive
            pytest.fail(f"Failed to read CSV {data_path}: {exc}")

        assert rows, f"CSV file {data_path} is empty"