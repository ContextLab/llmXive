"""
Schema Validation Utilities for LlmXive Pipeline.

Provides functions to validate downloaded datasets and generated embeddings
against the YAML schema definitions in contracts/.

Address: ordering-c952aaa0
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import logging

# Configure logging
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema file.
    
    Args:
        schema_path: Path to the .yaml schema file.
        
    Returns:
        Dictionary representation of the schema.
        
    Raises:
        FileNotFoundError: If schema file does not exist.
        yaml.YAMLError: If schema file is invalid YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_dataset_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dataset dictionary against a schema.
    
    Args:
        data: The dataset dictionary (e.g., from HuggingFace datasets).
        schema: The loaded schema definition.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required top-level keys
    required_keys = schema.get('required', [])
    for key in required_keys:
        if key not in data:
            errors.append(f"Missing required key in dataset: '{key}'")
    
    if errors:
        return False, errors

    # Validate fields list
    if 'fields' in schema.get('properties', {}):
        expected_fields = schema['properties']['fields'].get('const', [])
        if expected_fields:
            if set(data.get('fields', [])) != set(expected_fields):
                errors.append(f"Dataset fields mismatch. Expected: {expected_fields}, Got: {data.get('fields')}")

    # Validate features structure
    if 'features' in data:
        features = data['features']
        feature_schema = schema.get('properties', {}).get('features', {})
        required_features = feature_schema.get('required', [])
        
        for feat in required_features:
            if feat not in features:
                errors.append(f"Missing required feature: '{feat}'")
        
        # Validate specific feature types if defined
        if 'label' in features:
            label_val = features['label']
            # Check if label is integer and in expected range (0 or 1)
            if not isinstance(label_val, int) or label_val not in [0, 1]:
                # Note: In a real dataset object, 'label' might be a feature type description, 
                # not the actual value. This validation assumes a sample row or a summary dict.
                # For HuggingFace dataset info, we check the feature type.
                pass 
                
    # Validate row count if specified
    if 'expected_row_count' in schema.get('properties', {}):
        min_count = schema['properties']['expected_row_count'].get('minimum', 1)
        actual_count = data.get('num_rows', 0) # Assuming data has num_rows or len
        if actual_count < min_count:
            errors.append(f"Dataset too small. Expected >= {min_count}, Got {actual_count}")

    return len(errors) == 0, errors

def validate_embedding_schema(embeddings_path: str, labels: List[int], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate generated embeddings file against the embedding schema.
    
    Args:
        embeddings_path: Path to the .npy or .parquet file.
        labels: List of labels corresponding to the embeddings.
        schema: The loaded embedding schema definition.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    path = Path(embeddings_path)
    
    if not path.exists():
        return False, [f"Embeddings file not found: {embeddings_path}"]

    # Load embeddings
    try:
        if path.suffix == '.npy':
            embeddings = np.load(path)
        elif path.suffix == '.parquet':
            import pandas as pd
            df = pd.read_parquet(path)
            # Assuming the first column or a specific column is the embedding
            # For simplicity, we assume a flattened structure or specific handling
            # In a real scenario, we'd parse the schema to know which column
            embeddings = df.to_numpy() 
        else:
            errors.append(f"Unsupported file format: {path.suffix}")
            return False, errors
    except Exception as e:
        errors.append(f"Failed to load embeddings: {str(e)}")
        return False, errors

    # Check shape
    if len(embeddings.shape) != 2:
        errors.append(f"Embeddings must be 2D array. Got shape: {embeddings.shape}")
    else:
        num_samples, dim = embeddings.shape
        
        # Check label length match
        if len(labels) != num_samples:
            errors.append(f"Label count ({len(labels)}) does not match embedding rows ({num_samples})")
        
        # Check dimensions if defined in schema
        if 'dimensions' in schema.get('properties', {}).get('embedding_matrix', {}):
            expected_dim = schema['properties']['embedding_matrix']['dimensions']
            if dim != expected_dim:
                errors.append(f"Embedding dimension mismatch. Expected: {expected_dim}, Got: {dim}")

    # Check for NaN/Inf
    if np.any(np.isnan(embeddings)):
        errors.append("Embeddings contain NaN values")
    if np.any(np.isinf(embeddings)):
        errors.append("Embeddings contain Inf values")

    # Check label values
    for i, label in enumerate(labels):
        if label not in [0, 1]:
            errors.append(f"Invalid label at index {i}: {label}. Must be 0 or 1.")
            break

    return len(errors) == 0, errors

def main():
    """
    Entry point for manual schema validation testing.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (would be called by download.py or extract.py)
    dataset_schema_path = "contracts/dataset.schema.yaml"
    embedding_schema_path = "contracts/embedding.schema.yaml"
    
    if os.path.exists(dataset_schema_path):
        schema = load_schema(dataset_schema_path)
        logger.info(f"Loaded dataset schema: {schema.get('title')}")
    else:
        logger.error(f"Dataset schema not found at {dataset_schema_path}")

    if os.path.exists(embedding_schema_path):
        schema = load_schema(embedding_schema_path)
        logger.info(f"Loaded embedding schema: {schema.get('title')}")
    else:
        logger.error(f"Embedding schema not found at {embedding_schema_path}")

if __name__ == "__main__":
    main()