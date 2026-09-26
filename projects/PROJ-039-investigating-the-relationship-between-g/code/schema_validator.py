"""
Schema validation utilities for the Gut Microbiome - EEG Alpha Power project.
Validates data against contracts/dataset.schema.yaml and contracts/output.schema.yaml.
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    print("ERROR: jsonschema library is required. Install via: pip install jsonschema")
    sys.exit(1)

from config import get_project_root
from logging_config import get_logger

logger = get_logger(__name__)

# Paths relative to project root
PROJECT_ROOT = get_project_root()
DATASET_SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = PROJECT_ROOT / "contracts" / "output.schema.yaml"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON Schema from a YAML file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

class SchemaValidator:
    """Validates data dictionaries against defined schemas."""
    
    def __init__(self):
        self.dataset_schema = load_schema(DATASET_SCHEMA_PATH)
        self.output_schema = load_schema(OUTPUT_SCHEMA_PATH)
        self.dataset_validator = Draft7Validator(self.dataset_schema)
        self.output_validator = Draft7Validator(self.output_schema)

    def validate_dataset_record(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a single dataset record (row) against the dataset schema.
        Returns (is_valid, error_message).
        """
        errors = list(self.dataset_validator.iter_errors(record))
        if errors:
            error_msgs = [f"{e.path}: {e.message}" for e in errors]
            return False, "; ".join(error_msgs)
        return True, None

    def validate_output_record(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate a single output record (stratum summary) against the output schema.
        Returns (is_valid, error_message).
        """
        errors = list(self.output_validator.iter_errors(record))
        if errors:
            error_msgs = [f"{e.path}: {e.message}" for e in errors]
            return False, "; ".join(error_msgs)
        return True, None

    def validate_artifacts(self, artifact_path: Path, schema_type: str = "output") -> bool:
        """
        Validate a JSON artifact file against the appropriate schema.
        schema_type: 'dataset' or 'output'
        """
        if not artifact_path.exists():
            logger.error(f"Artifact file not found: {artifact_path}")
            return False

        try:
            with open(artifact_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {artifact_path}: {e}")
            return False

        if schema_type == "output":
            validator = self.output_validator
        elif schema_type == "dataset":
            validator = self.dataset_validator
        else:
            logger.error(f"Unknown schema type: {schema_type}")
            return False

        errors = list(validator.iter_errors(data))
        if errors:
            for error in errors:
                path_str = ".".join(map(str, error.path))
                logger.error(f"Validation error at {path_str}: {error.message}")
            return False

        logger.info(f"Artifact {artifact_path} validated successfully against {schema_type} schema.")
        return True

def main():
    """Run schema validation on known artifacts."""
    # Define artifacts to validate based on project structure
    artifacts_to_check = [
        ("artifacts/strata_report.json", "output"),
        ("artifacts/correlation_results.json", "output"), # Assuming it follows output-like structure or needs specific schema
        ("artifacts/analysis_results.json", "output"),
    ]

    validator = SchemaValidator()
    all_passed = True

    for rel_path, schema_type in artifacts_to_check:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            if not validator.validate_artifacts(full_path, schema_type):
                all_passed = False
        else:
            logger.warning(f"Skipping validation, file not found: {full_path}")

    if not all_passed:
        logger.error("Schema validation failed for one or more artifacts.")
        sys.exit(1)
    else:
        logger.info("All artifacts passed schema validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()
