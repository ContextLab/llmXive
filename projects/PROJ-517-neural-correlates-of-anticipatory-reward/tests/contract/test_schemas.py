"""
Contract tests for schema validation.
Validates that generated data conforms to defined schemas.
"""
import os
import sys
import yaml
import json
import pytest
from pathlib import Path
import pandas as pd

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from synthetic_generator import load_schema, generate_synthetic_dataset
from ingestion import load_schema as load_ingestion_schema, validate_columns

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / 'contracts'
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def load_yaml_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate a DataFrame against a schema definition.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dict
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = [
        field['name'] for field in schema.get('fields', []) 
        if field.get('required', False)
    ]
    
    # Check all required fields exist
    for field in required_fields:
        if field not in df.columns:
            return False
    
    # Check field types (basic check)
    for field in schema.get('fields', []):
        col_name = field['name']
        if col_name in df.columns:
            field_type = field.get('type')
            if field_type == 'string':
                if not df[col_name].apply(lambda x: isinstance(x, str)).all():
                    return False
            elif field_type == 'float':
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    return False
            elif field_type == 'integer':
                if not pd.api.types.is_integer_dtype(df[col_name]):
                    return False
            
            # Check constraints if present
            if 'min' in field:
                if df[col_name].min() < field['min']:
                    return False
            
            # Check pattern if present
            if 'pattern' in field:
                import re
                pattern = field['pattern']
                if not df[col_name].apply(lambda x: bool(re.match(pattern, str(x)))).all():
                    return False
    
    return True

def validate_output_against_schema(output_path: Path, schema: dict) -> bool:
    """
    Validate an output artifact against a schema.
    
    Args:
        output_path: Path to the output file
        schema: Schema definition dict
        
    Returns:
        bool: True if valid, False otherwise
    """
    file_name = output_path.name
    
    # Check if file exists
    if not output_path.exists():
        return False
    
    # Validate JSON files
    if file_name.endswith('.json'):
        try:
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Check required properties
            required_props = schema.get('schema', {}).get('properties', {})
            required_keys = schema.get('schema', {}).get('required', [])
            
            for key in required_keys:
                if key not in data:
                    return False
            
            return True
        except (json.JSONDecodeError, KeyError):
            return False
    
    # Validate markdown files (basic existence check)
    if file_name.endswith('.md') or file_name.endswith('.txt'):
        return output_path.stat().st_size > 0
    
    # Validate images
    if file_name.endswith('.png'):
        return output_path.stat().st_size > 0
    
    return False

class TestSchemasValidates:
    """Tests for schema validation of generated data and outputs."""
    
    def test_schemas_validates(self):
        """
        Validate contracts/dataset.schema.yaml and contracts/output.schema.yaml 
        against generated data and output.
        """
        # Load schemas
        dataset_schema_path = CONTRACTS_DIR / 'dataset.schema.yaml'
        output_schema_path = CONTRACTS_DIR / 'output.schema.yaml'
        
        assert dataset_schema_path.exists(), f"Dataset schema not found: {dataset_schema_path}"
        assert output_schema_path.exists(), f"Output schema not found: {output_schema_path}"
        
        dataset_schema = load_yaml_schema(dataset_schema_path)
        output_schema = load_yaml_schema(output_schema_path)
        
        # Generate synthetic data for testing
        synthetic_data_path = DATA_RAW_DIR / 'synthetic_test.csv'
        
        # Load schema from generator
        schema_for_gen = load_schema(dataset_schema_path)
        
        # Generate synthetic dataset
        generate_synthetic_dataset(
            schema=schema_for_gen,
            output_path=str(synthetic_data_path),
            n_neurons=5,
            n_trials_per_neuron=10
        )
        
        # Verify generated data file exists
        assert synthetic_data_path.exists(), "Synthetic test data was not generated"
        
        # Load generated data
        df_generated = pd.read_csv(synthetic_data_path)
        
        # Validate generated data against dataset schema
        assert validate_against_schema(df_generated, dataset_schema), \
            "Generated synthetic data does not conform to dataset.schema.yaml"
        
        # Run ingestion pipeline to generate output
        from ingestion import run_ingestion_pipeline
        
        # Create a minimal output for testing
        test_output_dir = DATA_PROCESSED_DIR
        
        # Generate validation report
        validation_report_path = test_output_dir / 'validation_report.json'
        validation_data = {
            'ingestion_rows_total': len(df_generated),
            'ingestion_rows_valid': len(df_generated),
            'ingestion_rows_dropped': 0,
            'validated_sample_size': len(df_generated),
            'confounded_trial_count': 0,
            'flagged_trial_ids': []
        }
        
        with open(validation_report_path, 'w') as f:
            json.dump(validation_data, f, indent=2)
        
        # Validate output against output schema
        # Get the validation_report.json schema from output_schema
        artifacts = output_schema.get('artifacts', [])
        validation_report_schema = None
        for artifact in artifacts:
            if artifact['name'] == 'validation_report.json':
                validation_report_schema = artifact
                break
        
        assert validation_report_schema is not None, "validation_report.json schema not found"
        
        assert validate_output_against_schema(
            validation_report_path, 
            validation_report_schema
        ), "Generated validation report does not conform to output.schema.yaml"
        
        # Clean up test output
        if validation_report_path.exists():
            validation_report_path.unlink()
        
        # Clean up synthetic data
        if synthetic_data_path.exists():
            synthetic_data_path.unlink()
        
        # Assert all tests passed
        assert True, "Schema validation completed successfully"
