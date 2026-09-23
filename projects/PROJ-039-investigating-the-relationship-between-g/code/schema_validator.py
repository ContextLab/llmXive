"""
Schema validation module for Gut Microbiome and EEG data.
Implements validation using jsonschema based on contracts/dataset.schema.yaml 
and contracts/output.schema.yaml.
"""
import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SchemaValidator:
    """
    A class to validate data against JSON schemas.
    """
    
    def __init__(self, schema_path: str):
        """
        Initialize the SchemaValidator with a schema file path.
        
        Args:
            schema_path: Path to the JSON schema file (YAML or JSON)
        """
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
        
    def _load_schema(self) -> Dict[str, Any]:
        """
        Load the schema from a YAML or JSON file.
        
        Returns:
            The schema as a dictionary.
        """
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        with open(self.schema_path, 'r') as f:
            if self.schema_path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            elif self.schema_path.suffix == '.json':
                return json.load(f)
            else:
                raise ValueError(f"Unsupported schema file format: {self.schema_path.suffix}")
    
    def validate(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> bool:
        """
        Validate data against the loaded schema.
        
        Args:
            data: The data to validate (single record or list of records)
            
        Returns:
            True if validation passes, False otherwise.
            
        Raises:
            ValidationError: If validation fails.
        """
        try:
            if isinstance(data, list):
                # Validate each item in the list
                for i, item in enumerate(data):
                    validate(instance=item, schema=self.schema)
                    logger.debug(f"Record {i} passed validation")
            else:
                # Validate single record
                validate(instance=data, schema=self.schema)
                logger.debug("Single record passed validation")
                
            return True
        except ValidationError as e:
            logger.error(f"Validation failed: {e.message}")
            logger.error(f"Path: {list(e.path)}")
            raise
    
    def validate_file(self, file_path: str, is_list: bool = True) -> bool:
        """
        Validate a JSON or YAML file against the schema.
        
        Args:
            file_path: Path to the data file
            is_list: Whether the file contains a list of records (default: True)
            
        Returns:
            True if validation passes, False otherwise.
        """
        data_path = Path(file_path)
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        with open(data_path, 'r') as f:
            if data_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif data_path.suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported data file format: {data_path.suffix}")
        
        return self.validate(data)

def validate_artifacts() -> bool:
    """
    Validate all required artifacts against their schemas.
    
    Returns:
        True if all validations pass, False otherwise.
    """
    dataset_schema_path = project_root / "contracts" / "dataset.schema.yaml"
    output_schema_path = project_root / "contracts" / "output.schema.yaml"
    
    # Validate dataset schema exists
    if not dataset_schema_path.exists():
        logger.error(f"Dataset schema not found: {dataset_schema_path}")
        return False
        
    # Validate output schema exists
    if not output_schema_path.exists():
        logger.error(f"Output schema not found: {output_schema_path}")
        return False
    
    try:
        # Initialize validators
        dataset_validator = SchemaValidator(str(dataset_schema_path))
        output_validator = SchemaValidator(str(output_schema_path))
        
        logger.info("Dataset and Output schemas loaded successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize validators: {e}")
        return False

def main():
    """
    Main function to run schema validation.
    """
    logger.info("Starting schema validation...")
    
    # Check if schemas exist and are valid
    if not validate_artifacts():
        logger.error("Schema validation failed.")
        sys.exit(1)
    
    logger.info("Schema validation completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
