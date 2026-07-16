"""
Schema validation module for enforcing contract validation on all data writes.

This module provides utilities to validate data against JSON schemas defined in
the contracts directory before writing to disk.
"""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from src.config import get_contract_path, ensure_directories

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
except ImportError:
    # If jsonschema is not installed, we cannot perform validation
    # This should be caught during execution and fail loudly
    raise ImportError(
        "jsonschema package is required for schema validation. "
        "Install it via: pip install jsonschema"
    )

class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass

class SchemaValidator:
    """
    A class to handle schema validation for data writes.
    
    Attributes:
        schema_path (Path): Path to the JSON schema file.
        schema (Dict): The loaded JSON schema.
        validator (Draft7Validator): The validator instance.
    """
    
    def __init__(self, schema_name: str):
        """
        Initialize the SchemaValidator with a specific schema.
        
        Args:
            schema_name: Name of the schema file (e.g., 'injection.schema.yaml')
                        Note: Schemas are stored as .yaml but loaded as JSON-compatible dicts.
        """
        self.schema_path = get_contract_path(schema_name)
        
        if not self.schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        
        self.schema = self._load_schema()
        self.validator = Draft7Validator(self.schema)
    
    def _load_schema(self) -> Dict:
        """
        Load the JSON/YAML schema from disk.
        
        Returns:
            Dict: The loaded schema.
        
        Raises:
            json.JSONDecodeError: If the schema file is not valid JSON.
            FileNotFoundError: If the schema file doesn't exist.
        """
        # Handle both .json and .yaml files (treating YAML as JSON-compatible for simple schemas)
        # For this implementation, we assume schemas are valid JSON or simple YAML
        # that can be parsed by a YAML loader if available, or we expect JSON.
        # Given the task constraints, we'll try JSON first, then attempt a basic YAML parse
        # if jsonschema is used with YAML schemas (which requires PyYAML).
        
        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse as JSON first
            return json.loads(content)
        except json.JSONDecodeError:
            # If it's YAML, try to parse with PyYAML if available
            try:
                import yaml
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except ImportError:
                raise ImportError(
                    f"Schema file {self.schema_path} appears to be YAML, "
                    "but PyYAML is not installed. Install with: pip install pyyaml"
                )
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in schema file {self.schema_path}: {e}")
    
    def validate(self, data: Union[Dict, List]) -> bool:
        """
        Validate data against the loaded schema.
        
        Args:
            data: The data to validate (dict or list of dicts).
        
        Returns:
            bool: True if validation passes.
        
        Raises:
            SchemaValidationError: If validation fails.
        """
        errors = list(self.validator.iter_errors(data))
        
        if errors:
            error_messages = []
            for error in errors:
                path = " -> ".join(map(str, error.absolute_path)) if error.absolute_path else "root"
                error_messages.append(f"Error at {path}: {error.message}")
            
            raise SchemaValidationError(
                f"Schema validation failed for {self.schema_path.name}:\n" +
                "\n".join(error_messages)
            )
        
        return True
    
    def validate_and_save(self, data: Union[Dict, List], output_path: Union[str, Path]) -> None:
        """
        Validate data and save to disk if validation passes.
        
        Args:
            data: The data to validate and save.
            output_path: Path where the data will be saved.
        
        Raises:
            SchemaValidationError: If validation fails.
            IOError: If saving to disk fails.
        """
        # Ensure output directory exists
        output_path = Path(output_path)
        ensure_directories(str(output_path.parent))
        
        # Validate first
        self.validate(data)
        
        # Save if validation passes
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Update checksums after successful write
        from src.data_hygiene import update_checksum
        update_checksum(str(output_path))

def get_validator(schema_name: str) -> SchemaValidator:
    """
    Factory function to get a SchemaValidator instance.
    
    Args:
        schema_name: Name of the schema file.
    
    Returns:
        SchemaValidator: An instance configured for the specified schema.
    """
    return SchemaValidator(schema_name)

def validate_data(data: Union[Dict, List], schema_name: str) -> bool:
    """
    Convenience function to validate data against a schema.
    
    Args:
        data: The data to validate.
        schema_name: Name of the schema file.
    
    Returns:
        bool: True if validation passes.
    
    Raises:
        SchemaValidationError: If validation fails.
    """
    validator = get_validator(schema_name)
    return validator.validate(data)

def validate_and_save(data: Union[Dict, List], schema_name: str, output_path: Union[str, Path]) -> None:
    """
    Convenience function to validate and save data.
    
    Args:
        data: The data to validate and save.
        schema_name: Name of the schema file.
        output_path: Path where the data will be saved.
    
    Raises:
        SchemaValidationError: If validation fails.
        IOError: If saving to disk fails.
    """
    validator = get_validator(schema_name)
    validator.validate_and_save(data, output_path)

# Main entry point for CLI usage
if __name__ == "__main__":
    import argparse
    
    def main():
        parser = argparse.ArgumentParser(description="Validate data against a schema")
        parser.add_argument("data_file", help="Path to the data file (JSON)")
        parser.add_argument("schema_name", help="Name of the schema file (e.g., injection.schema.yaml)")
        parser.add_argument("--output", "-o", help="Optional output path if saving validated data")
        
        args = parser.parse_args()
        
        try:
            # Load data
            with open(args.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate
            validator = get_validator(args.schema_name)
            validator.validate(data)
            
            print(f"✓ Validation passed for {args.data_file} against {args.schema_name}")
            
            # Save if output path provided
            if args.output:
                validator.validate_and_save(data, args.output)
                print(f"✓ Saved validated data to {args.output}")
        
        except FileNotFoundError as e:
            print(f"✗ File not found: {e}", file=sys.stderr)
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"✗ Invalid JSON: {e}", file=sys.stderr)
            sys.exit(1)
        except SchemaValidationError as e:
            print(f"✗ {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"✗ Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)
    
    main()
