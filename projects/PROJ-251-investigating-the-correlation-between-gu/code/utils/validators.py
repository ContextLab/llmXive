import os
import yaml
import json
from typing import Dict, Any, List, Optional
from pathlib import Path

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataset_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a dataset dictionary against a schema.
    
    Args:
        data: Dictionary containing dataset keys and values.
        schema: Dictionary containing schema definition.
    
    Returns:
        Dictionary with validation results.
    """
    errors = []
    required = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required fields
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check field types
    for field, value in data.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type == 'number':
                if not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' should be a number, got {type(value).__name__}")
            elif expected_type == 'string':
                if not isinstance(value, str):
                    errors.append(f"Field '{field}' should be a string, got {type(value).__name__}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_correlation_results_schema(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate correlation results against expected schema.
    
    Args:
        data: List of dictionaries containing correlation results.
    
    Returns:
        Dictionary with validation results.
    """
    errors = []
    required_fields = ['taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue']
    
    if not isinstance(data, list):
        return {'valid': False, 'errors': ['Data must be a list of correlation results']}
    
    for i, item in enumerate(data):
        for field in required_fields:
            if field not in item:
                errors.append(f"Item {i} missing required field: {field}")
        
        # Check numeric fields
        for field in ['coefficient', 'raw_pvalue', 'adj_pvalue']:
            if field in item and not isinstance(item[field], (int, float)):
                errors.append(f"Item {i}, field '{field}' must be numeric")
        
        # Check p-value ranges
        if 'raw_pvalue' in item and not (0 <= item['raw_pvalue'] <= 1):
            errors.append(f"Item {i}, raw_pvalue out of range [0, 1]")
        if 'adj_pvalue' in item and not (0 <= item['adj_pvalue'] <= 1):
            errors.append(f"Item {i}, adj_pvalue out of range [0, 1]")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_model_metrics_schema(data: Dict[str, Any], schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate model metrics against expected schema.
    
    Args:
        data: Dictionary containing model metrics.
        schema_path: Optional path to YAML schema file.
    
    Returns:
        Dictionary with validation results.
    """
    errors = []
    required_fields = [
        'mean_accuracy', 'std_accuracy', 'meets_accuracy_target',
        'significance_pvalue', 'threshold_details'
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    # Check numeric fields
    numeric_fields = ['mean_accuracy', 'std_accuracy', 'significance_pvalue']
    for field in numeric_fields:
        if field in data and not isinstance(data[field], (int, float)):
            errors.append(f"Field '{field}' must be numeric")
    
    # Check boolean fields
    if 'meets_accuracy_target' in data and not isinstance(data['meets_accuracy_target'], bool):
        errors.append("Field 'meets_accuracy_target' must be boolean")
    
    # Check threshold_details structure
    if 'threshold_details' in data:
        if not isinstance(data['threshold_details'], list):
            errors.append("Field 'threshold_details' must be a list")
        else:
            for i, threshold in enumerate(data['threshold_details']):
                if not isinstance(threshold, dict):
                    errors.append(f"Threshold {i} must be a dictionary")
                elif 'accuracy' not in threshold:
                    errors.append(f"Threshold {i} missing 'accuracy' field")
    
    # Check ranges
    if 'mean_accuracy' in data and not (0 <= data['mean_accuracy'] <= 1):
        errors.append("mean_accuracy must be between 0 and 1")
    if 'significance_pvalue' in data and not (0 <= data['significance_pvalue'] <= 1):
        errors.append("significance_pvalue must be between 0 and 1")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def validate_schema_loads_yaml(schema_path: str) -> Dict[str, Any]:
    """
    Test that a schema can be loaded from YAML.
    
    Args:
        schema_path: Path to the YAML schema file.
    
    Returns:
        Dictionary with validation results.
    """
    try:
        schema = load_schema(schema_path)
        return {
            'valid': True,
            'schema': schema,
            'errors': []
        }
    except Exception as e:
        return {
            'valid': False,
            'schema': None,
            'errors': [str(e)]
        }
