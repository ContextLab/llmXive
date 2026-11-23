"""
Contract test for the featurized dataset JSONL file.

This test validates each record in ``data/processed/featurized.jsonl`` against the
JSON Schema defined in ``specs/001-predicting-molecular-diffusion-coefficie/contracts/dataset.schema.yaml``.
It is executed by ``pytest`` during the CI run.
"""

import json
import yaml
import jsonschema
from pathlib import Path

def _load_schema() -> dict:
    """
    Load the JSON schema from the specifications directory.
    """
    # Resolve the path to the repository root (two levels up from this file)
    repo_root = Path(__file__).resolve().parents[2]
    schema_path = (
        repo_root
        / "specs"
        / "001-predicting-molecular-diffusion-coefficie"
        / "contracts"
        / "dataset.schema.yaml"
    )
    if not schema_path.is_file():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _load_featurized_jsonl() -> Path:
    """
    Return the path to the featurized JSONL file produced by the ingestion pipeline.
    """
    repo_root = Path(__file__).resolve().parents[2]
    jsonl_path = repo_root / "data" / "processed" / "featurized.jsonl"
    if not jsonl_path.is_file():
        raise FileNotFoundError(
            f"Featurized dataset not found at {jsonl_path}. "
            "Run the ingestion pipeline before executing contract tests."
        )
    return jsonl_path

def test_featurized_dataset_schema():
    """
    Validate every record in the JSONL file against the schema.
    """
    schema = _load_schema()
    jsonl_path = _load_featurized_jsonl()

    with jsonl_path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            # Skip empty lines that may appear at the end of the file
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"Line {line_number} is not valid JSON: {exc}"
                ) from exc

            try:
                jsonschema.validate(instance=record, schema=schema)
            except jsonschema.ValidationError as exc:
                raise AssertionError(
                    f"Record on line {line_number} failed schema validation: {exc.message}"
                ) from exc
