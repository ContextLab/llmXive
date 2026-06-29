"""
Schema validators for GitHub issue data against contracts/ definitions.

Implements SC-001: Schema validation for all data artifacts.
Validates raw API responses, processed datasets, and analysis outputs.
"""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import yaml

from utils.config import get_path


class ValidationError(Exception):
    """Raised when schema validation fails."""
    def __init__(self, message: str, field: str = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class SchemaValidator:
    """
    Validates data structures against YAML schema definitions from contracts/.
    
    SC-001 Compliance: All data artifacts must pass schema validation before
    being written to disk or consumed by downstream tasks.
    """

    def __init__(self, contracts_dir: Path = None):
        """Initialize validator with path to contracts directory."""
        if contracts_dir is None:
            contracts_dir = get_path("contracts")
        self.contracts_dir = contracts_dir

    def load_schema(self, schema_name: str) -> Dict[str, Any]:
        """
        Load a schema definition from contracts/.
        
        Args:
            schema_name: Name of schema file (without .yaml extension)
        
        Returns:
            Schema definition as dictionary
        
        Raises:
            FileNotFoundError: If schema file doesn't exist
        """
        schema_path = self.contracts_dir / f"{schema_name}_schema.yaml"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def validate_type(self, value: Any, expected_type: str, field: str) -> bool:
        """
        Validate that a value matches the expected type.
        
        Args:
            value: The value to validate
            expected_type: Expected type name (string, integer, number, boolean, array, object)
            field: Field name for error messages
        
        Returns:
            True if type matches
        
        Raises:
            ValidationError: If type doesn't match
        """
        type_mapping = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'array': list,
            'object': dict,
        }

        if expected_type not in type_mapping:
            raise ValidationError(f"Unknown type '{expected_type}' for field '{field}'")

        expected_python_type = type_mapping[expected_type]
        
        if not isinstance(value, expected_python_type):
            raise ValidationError(
                f"Field '{field}' has type '{type(value).__name__}', expected '{expected_type}'",
                field=field,
                value=value
            )
        
        return True

    def validate_required(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """
        Validate that all required fields are present.
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
        
        Raises:
            ValidationError: If any required field is missing
        """
        missing = [f for f in required_fields if f not in data]
        if missing:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing)}",
                field=missing[0]
            )

    def validate_field_constraints(self, value: Any, constraints: Dict[str, Any], field: str) -> None:
        """
        Validate value against field constraints (min, max, pattern, enum, etc.).
        
        Args:
            value: The value to validate
            constraints: Dictionary of constraint definitions
            field: Field name for error messages
        
        Raises:
            ValidationError: If constraints are violated
        """
        if 'min' in constraints and value < constraints['min']:
            raise ValidationError(
                f"Field '{field}' value {value} is below minimum {constraints['min']}",
                field=field,
                value=value
            )
        
        if 'max' in constraints and value > constraints['max']:
            raise ValidationError(
                f"Field '{field}' value {value} exceeds maximum {constraints['max']}",
                field=field,
                value=value
            )
        
        if 'pattern' in constraints and isinstance(value, str):
            import re
            if not re.match(constraints['pattern'], value):
                raise ValidationError(
                    f"Field '{field}' value '{value}' does not match pattern '{constraints['pattern']}'",
                    field=field,
                    value=value
                )
        
        if 'enum' in constraints and value not in constraints['enum']:
            raise ValidationError(
                f"Field '{field}' value '{value}' not in allowed values: {constraints['enum']}",
                field=field,
                value=value
            )
        
        if 'min_length' in constraints and isinstance(value, str):
            if len(value) < constraints['min_length']:
                raise ValidationError(
                    f"Field '{field}' length {len(value)} is below minimum {constraints['min_length']}",
                    field=field,
                    value=value
                )

    def validate_record(self, record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """
        Validate a single record against a schema definition.
        
        Args:
            record: Dictionary representing a single record/row
            schema: Schema definition dictionary
        
        Returns:
            List of validation error messages (empty if valid)
        
        Raises:
            ValidationError: If validation fails
        """
        errors = []
        
        # Check required fields
        required = schema.get('required', [])
        self.validate_required(record, required)
        
        # Validate each field
        properties = schema.get('properties', {})
        for field_name, field_schema in properties.items():
            if field_name not in record:
                continue  # Already handled by required check
            
            value = record[field_name]
            
            # Type validation
            expected_type = field_schema.get('type')
            if expected_type:
                try:
                    self.validate_type(value, expected_type, field_name)
                except ValidationError as e:
                    errors.append(str(e))
                    continue  # Skip constraint validation if type is wrong
            
            # Constraint validation
            constraints = {k: v for k, v in field_schema.items() 
                         if k in ['min', 'max', 'pattern', 'enum', 'min_length']}
            if constraints:
                try:
                    self.validate_field_constraints(value, constraints, field_name)
                except ValidationError as e:
                    errors.append(str(e))
        
        return errors

    def validate_dataset(self, data: List[Dict[str, Any]], schema_name: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate an entire dataset (list of records) against a schema.
        
        Args:
            data: List of dictionaries representing dataset rows
            schema_name: Name of schema to validate against
        
        Returns:
            Tuple of (is_valid, validation_report)
        
        SC-001 Compliance: Returns detailed report with completeness metrics.
        """
        schema = self.load_schema(schema_name)
        
        total_records = len(data)
        valid_records = 0
        invalid_records = []
        field_stats = {}
        
        for idx, record in enumerate(data):
            errors = self.validate_record(record, schema)
            
            if not errors:
                valid_records += 1
            else:
                invalid_records.append({
                    'index': idx,
                    'errors': errors
                })
            
            # Track field presence
            properties = schema.get('properties', {})
            for field_name in properties:
                if field_name not in field_stats:
                    field_stats[field_name] = {'present': 0, 'total': total_records}
                if field_name in record:
                    field_stats[field_name]['present'] += 1
        
        completeness = {
            field: stats['present'] / stats['total'] if stats['total'] > 0 else 0
            for field, stats in field_stats.items()
        }
        
        validation_report = {
            'schema_name': schema_name,
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': len(invalid_records),
            'validity_rate': valid_records / total_records if total_records > 0 else 0,
            'completeness': completeness,
            'errors': invalid_records[:10],  # Limit to first 10 errors
            'passed': len(invalid_records) == 0
        }
        
        return validation_report['passed'], validation_report

    def validate_raw_issue(self, issue_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate raw GitHub API issue response.
        
        Args:
            issue_data: Dictionary from GitHub API
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        schema = self.load_schema('raw_issue')
        errors = self.validate_record(issue_data, schema)
        return len(errors) == 0, errors

    def validate_processed_issue(self, issue_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate processed/cleaned issue record.
        
        Args:
            issue_data: Dictionary from preprocessing pipeline
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        schema = self.load_schema('processed_issue')
        errors = self.validate_record(issue_data, schema)
        return len(errors) == 0, errors

    def validate_analysis_output(self, output_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate analysis output (distribution metrics, test results).
        
        Args:
            output_data: Dictionary from analysis scripts
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        schema = self.load_schema('analysis_output')
        errors = self.validate_record(output_data, schema)
        return len(errors) == 0, errors


def get_validator() -> SchemaValidator:
    """Factory function to get a SchemaValidator instance."""
    return SchemaValidator()


def validate_dataset_schema(data_path: str, schema_name: str) -> Dict[str, Any]:
    """
    Convenience function to validate a JSON/CSV dataset against a schema.
    
    Args:
        data_path: Path to data file (JSON or CSV)
        schema_name: Name of schema to validate against
    
    Returns:
        Validation report dictionary
    
    SC-001 Compliance: Used by T011 to validate cleaned_issues.csv.
    """
    validator = get_validator()
    schema = validator.load_schema(schema_name)
    
    # Load data based on file extension
    path = Path(data_path)
    if path.suffix == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif path.suffix == '.csv':
        import pandas as pd
        data = pd.read_csv(path).to_dict('records')
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    return validator.validate_dataset(data, schema_name)

# Ensure contracts directory exists for validators
def ensure_contracts_dir():
    """Create contracts directory if it doesn't exist."""
    contracts_dir = get_path("contracts")
    contracts_dir.mkdir(parents=True, exist_ok=True)
    return contracts_dir
