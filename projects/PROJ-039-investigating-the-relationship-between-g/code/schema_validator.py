import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from jsonschema import validate, ValidationError, Draft7Validator
from config import get_project_root

logger = logging.getLogger(__name__)

class SchemaValidator:
    """
    Validates data against JSON schemas defined in contracts/
    """

    def __init__(self, schema_path: str):
        """
        Initialize validator with a schema file.

        Args:
            schema_path: Path to the YAML schema file relative to project root
        """
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)

    def _load_schema(self) -> Dict[str, Any]:
        """Load schema from YAML file."""
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, 'r') as f:
            return yaml.safe_load(f)

    def validate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """
        Validate data against the schema.

        Args:
            data: Data to validate (single record or list of records)

        Returns:
            True if valid, raises ValidationError if invalid

        Raises:
            ValidationError: If data does not conform to schema
        """
        if isinstance(data, list):
            for i, record in enumerate(data):
                try:
                    validate(instance=record, schema=self.schema)
                except ValidationError as e:
                    logger.error(f"Validation error in record {i}: {e.message}")
                    raise
        else:
            validate(instance=data, schema=self.schema)
        
        logger.info(f"Data validation successful against {self.schema_path}")
        return True

    def validate_file(self, file_path: str) -> bool:
        """
        Validate a JSON/CSV file against the schema.

        Args:
            file_path: Path to the file to validate

        Returns:
            True if valid

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        
        if ext == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
        elif ext == '.csv':
            import pandas as pd
            df = pd.read_csv(file_path)
            data = df.to_dict(orient='records')
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return self.validate(data)

def validate_artifacts() -> bool:
    """
    Validate all key artifacts against their respective schemas.

    Returns:
        True if all validations pass, False otherwise
    """
    project_root = get_project_root()
    contracts_dir = project_root / "contracts"
    data_dir = project_root / "data" / "processed"
    artifacts_dir = project_root / "artifacts"

    all_valid = True

    # Validate dataset schema against processed microbiome and EEG data
    dataset_schema = contracts_dir / "dataset.schema.yaml"
    if dataset_schema.exists():
        validator = SchemaValidator(str(dataset_schema.relative_to(project_root)))
        
        # Check if processed data files exist before validating
        microbiome_file = data_dir / "microbiome_features.csv"
        eeg_file = data_dir / "eeg_features.csv"
        
        if microbiome_file.exists():
            try:
                validator.validate_file(str(microbiome_file))
                logger.info(f"✓ {microbiome_file} valid against dataset schema")
            except Exception as e:
                logger.error(f"✗ {microbiome_file} failed validation: {e}")
                all_valid = False
        
        if eeg_file.exists():
            try:
                validator.validate_file(str(eeg_file))
                logger.info(f"✓ {eeg_file} valid against dataset schema")
            except Exception as e:
                logger.error(f"✗ {eeg_file} failed validation: {e}")
                all_valid = False

    # Validate output schema against stratum features
    output_schema = contracts_dir / "output.schema.yaml"
    if output_schema.exists():
        validator = SchemaValidator(str(output_schema.relative_to(project_root)))
        
        stratum_file = data_dir / "stratum_features.csv"
        if stratum_file.exists():
            try:
                validator.validate_file(str(stratum_file))
                logger.info(f"✓ {stratum_file} valid against output schema")
            except Exception as e:
                logger.error(f"✗ {stratum_file} failed validation: {e}")
                all_valid = False
        
        # Also validate strata_report.json if it exists
        strata_report = artifacts_dir / "strata_report.json"
        if strata_report.exists():
            try:
                validator.validate_file(str(strata_report))
                logger.info(f"✓ {strata_report} valid against output schema")
            except Exception as e:
                logger.error(f"✗ {strata_report} failed validation: {e}")
                all_valid = False

    return all_valid

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    success = validate_artifacts()
    if success:
        print("All artifacts validated successfully.")
        exit(0)
    else:
        print("Validation failed for one or more artifacts.")
        exit(1)
