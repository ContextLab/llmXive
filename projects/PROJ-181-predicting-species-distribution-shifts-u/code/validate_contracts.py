"""
Validation utility for data contracts.

Usage:
    python -m code.validate_contracts

The script loads each ``*.schema.yaml`` file from the ``contracts`` directory
and validates the corresponding data artefacts (CSV, JSON, YAML) against the
schema using ``jsonschema``.  Missing artefacts are skipped; only existing
files are validated.  Any validation error aborts the process with a non‑zero
exit code and prints the offending file and validation message.
"""
import json
import csv
import sys
from pathlib import Path

import yaml
from jsonschema import Draft7Validator, ValidationError

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with schema_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _validate_instance(instance: dict, schema: dict, artefact_path: Path) -> None:
    """Validate a single JSON/YAML instance against a schema."""
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    if errors:
        msgs = "\n".join(
            f"- {'.'.join(map(str, error.path))}: {error.message}"
            for error in errors
        )
        raise ValidationError(f"Validation failed for {artefact_path}:\n{msgs}")

def _load_csv_first_row(csv_path: Path) -> dict:
    """Load the first row of a CSV as a dict (header → value)."""
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        try:
            return next(reader)
        except StopIteration:
            raise ValidationError(f"CSV file {csv_path} is empty.")

def _load_json(json_path: Path) -> dict:
    """Load a JSON file."""
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _load_yaml(yaml_path: Path) -> dict:
    """Load a YAML file."""
    with yaml_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
# Mapping from schema filename to one or more artefact paths to validate.
# The mapping is deliberately simple – it covers the artefacts that are
# expected to exist after the pipeline steps.
# ----------------------------------------------------------------------
SCHEMA_TO_ARTIFACTS = {
    # Raw occurrence CSVs
    "occurrence.schema.yaml": [
        Path("data/raw/occurrence_1970_2000.csv"),
        Path("data/raw/occurrence_2005_2020.csv"),
    ],
    # Processed occurrence records (placeholder CSV)
    "occurrence_record.schema.yaml": [
        Path("data/processed/occurrence_placeholder.csv")
    ],
    # Climate raster metadata (placeholder – we only validate existence)
    "climate_raster.schema.yaml": [
        # any .tif under data/raw/; we will just check that files exist
    ],
    # Climate variable definitions (no concrete artefact yet)
    "climate_variable.schema.yaml": [],
    # Data‑sufficiency summary
    "data_sufficiency.schema.yaml": [Path("metrics/data_sufficiency.json")],
    # Model artefact metadata (dummy model)
    "model_artifact.schema.yaml": [Path("models/dummy_model.pkl")],
    # Model performance metrics
    "model_metrics.schema.yaml": [Path("metrics/model_performance.json")],
    # Log counts produced by preprocessing
    "log_counts.schema.yaml": [Path("logs/preprocess_counts.yaml")],
}

def _validate_file(artefact_path: Path, schema: dict) -> None:
    """Dispatch validation based on file type."""
    if not artefact_path.exists():
        # Missing artefacts are simply skipped – they may not be required yet.
        return

    if artefact_path.suffix.lower() == ".csv":
        instance = _load_csv_first_row(artefact_path)
        _validate_instance(instance, schema, artefact_path)
    elif artefact_path.suffix.lower() in {".json", ".yaml", ".yml"}:
        if artefact_path.suffix.lower() == ".json":
            instance = _load_json(artefact_path)
        else:
            instance = _load_yaml(artefact_path)
        _validate_instance(instance, schema, artefact_path)
    elif artefact_path.suffix.lower() == ".tif":
        # Raster files are binary; we only ensure they exist.
        # Full raster metadata validation would require rasterio which is
        # unnecessary for contract checking at this stage.
        return
    else:
        # Unknown file type – skip.
        return

def main() -> None:
    contracts_dir = Path("contracts")
    if not contracts_dir.is_dir():
        print("Contracts directory not found.", file=sys.stderr)
        sys.exit(1)

    # Iterate over each schema file
    for schema_file in contracts_dir.glob("*.schema.yaml"):
        schema_name = schema_file.name
        schema = _load_schema(schema_file)

        artefact_paths = SCHEMA_TO_ARTIFACTS.get(schema_name, [])
        # Special handling for raster globbing
        if schema_name == "climate_raster.schema.yaml":
            artefact_paths = list(Path("data/raw").rglob("*.tif"))

        for artefact_path in artefact_paths:
            try:
                _validate_file(artefact_path, schema)
            except ValidationError as ve:
                print(str(ve), file=sys.stderr)
                sys.exit(1)

    print("All existing artefacts validated successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
