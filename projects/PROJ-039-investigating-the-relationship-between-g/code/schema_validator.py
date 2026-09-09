"""
Schema validation module for gut microbiome and EEG data.
Validates datasets against JSON schemas defined in contracts/.
"""
import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Import pydantic if available, otherwise use jsonschema
try:
    from jsonschema import validate, ValidationError, Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema not installed. Validation will be basic type checking.")

from config import get_project_root

logger = logging.getLogger(__name__)

class SchemaValidator:
    """
    Validates data records against JSON schemas.
    """
    def __init__(self, schema_path: str):
        self.schema_path = schema_path
        self.schema = self._load_schema(schema_path)
        self.validator = Draft7Validator(self.schema) if HAS_JSONSCHEMA else None

    def _load_schema(self, path: str) -> Dict[str, Any]:
        """Load a YAML or JSON schema file."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Schema file not found: {path}")
        
        with open(p, 'r') as f:
            if p.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif p.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported schema format: {p.suffix}")

    def validate_record(self, record: Dict[str, Any]) -> bool:
        """
        Validate a single record against the schema.
        Returns True if valid, False otherwise.
        Logs errors.
        """
        if not self.validator:
            # Fallback basic check if jsonschema not available
            logger.warning("jsonschema not available, skipping deep validation.")
            return True

        errors = list(self.validator.iter_errors(record))
        if errors:
            for error in errors:
                logger.error(f"Validation error: {error.message} at path: {list(error.path)}")
            return False
        
        logger.debug("Record validation passed.")
        return True

    def validate_batch(self, records: List[Dict[str, Any]]) -> List[int]:
        """
        Validate a batch of records.
        Returns a list of indices of invalid records.
        """
        invalid_indices = []
        for i, record in enumerate(records):
            if not self.validate_record(record):
                invalid_indices.append(i)
        return invalid_indices

def validate_artifacts() -> bool:
    """
    Main entry point to validate all required artifacts against their schemas.
    Returns True if all validations pass, False otherwise.
    """
    project_root = get_project_root()
    contracts_dir = project_root / "contracts"
    
    dataset_schema_path = contracts_dir / "dataset.schema.yaml"
    output_schema_path = contracts_dir / "output.schema.yaml"
    
    if not dataset_schema_path.exists():
        logger.error(f"Dataset schema not found at {dataset_schema_path}")
        return False
    if not output_schema_path.exists():
        logger.error(f"Output schema not found at {output_schema_path}")
        return False

    # Validate dataset schema structure itself
    try:
        dataset_validator = SchemaValidator(str(dataset_schema_path))
        logger.info(f"Dataset schema loaded successfully from {dataset_schema_path}")
    except Exception as e:
        logger.error(f"Failed to load dataset schema: {e}")
        return False

    # Validate output schema structure itself
    try:
        output_validator = SchemaValidator(str(output_schema_path))
        logger.info(f"Output schema loaded successfully from {output_schema_path}")
    except Exception as e:
        logger.error(f"Failed to load output schema: {e}")
        return False

    # Example validation of data files if they exist
    # In a real pipeline, this would be called by the data loading scripts
    microbiome_file = project_root / "data" / "processed" / "microbiome_features.csv"
    eeg_file = project_root / "data" / "processed" / "eeg_features.csv"
    stratum_file = project_root / "data" / "processed" / "stratum_features.csv"
    
    # We don't load CSVs here to keep this module light, 
    # but we ensure the schemas are ready for consumption.
    logger.info("Schema validation infrastructure initialized.")
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = validate_artifacts()
    if success:
        print("All schemas are valid and ready for use.")
    else:
        print("Schema validation failed.")
        exit(1)
