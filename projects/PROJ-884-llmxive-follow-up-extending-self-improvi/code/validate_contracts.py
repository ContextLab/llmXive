"""Validate the contract schemas in contracts/.

T015: ensures contracts/dataset.schema.yaml and contracts/output.schema.yaml
exist, are syntactically valid YAML, and are structurally valid JSON Schema
(draft-07) documents. Writes a validation report to
data/processed/contract_validation.json.
"""
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

CONTRACTS = [
    "contracts/dataset.schema.yaml",
    "contracts/output.schema.yaml",
]
REPORT_PATH = Path("data/processed/contract_validation.json")


def validate_contract(path: Path) -> dict:
    """Validate one contract file. Returns a result dict; raises on failure."""
    if not path.is_file():
        raise FileNotFoundError(f"Contract file missing: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Contract file is empty: {path}")

    # Syntactic YAML validation (the task's observable check).
    schema = yaml.safe_load(text)
    if not isinstance(schema, dict):
        raise ValueError(f"Contract did not parse to a mapping: {path}")

    # Structural JSON Schema (draft-07) validation.
    Draft7Validator.check_schema(schema)

    return {
        "path": str(path),
        "valid_yaml": True,
        "valid_json_schema_draft07": True,
        "title": schema.get("title", ""),
        "bytes": len(text.encode("utf-8")),
    }


def main() -> int:
    results = []
    for rel in CONTRACTS:
        result = validate_contract(Path(rel))
        results.append(result)
        print(f"OK  {rel}: valid YAML and draft-07 JSON Schema "
              f"({result['title']})")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "all_valid": True,
        "contracts": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
