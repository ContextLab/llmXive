import os
import json
import logging
from typing import Dict, List, Any, Optional, Generator
import pandas as pd
import yaml
from pathlib import Path
from datasets import load_dataset

from logging_config import setup_logging

logger = setup_logging(__name__)

def ensure_dirs():
    """Ensure that required directories exist."""
    dirs = ['data/raw', 'data/processed', 'data/samples', 'logs']
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: str = "contracts/dataset.schema.yaml") -> Dict[str, Any]:
    """Load the dataset schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_fields(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate that a record contains all required fields defined in the schema.
    Raises ValueError if any required field is missing.
    """
    required_fields = schema.get('required', [])
    missing_fields = [field for field in required_fields if field not in record]
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")
    
    # Validate types if 'properties' is defined
    properties = schema.get('properties', {})
    for field, value in record.items():
        if field in properties:
            prop_def = properties[field]
            expected_type = prop_def.get('type')
            
            if expected_type == 'string' and not isinstance(value, str):
                raise TypeError(f"Field '{field}' must be a string, got {type(value)}")
            elif expected_type == 'array' and not isinstance(value, list):
                raise TypeError(f"Field '{field}' must be a list, got {type(value)}")
            elif expected_type == 'object' and not isinstance(value, dict):
                raise TypeError(f"Field '{field}' must be an object, got {type(value)}")
            
    return True

def fetch_gatemem(dataset_name: str = "llmXive/gatemem", split: str = "train") -> Generator[Dict[str, Any], None, None]:
    """
    Fetch the GateMem dataset from HuggingFace.
    Yields records one by one to handle large datasets efficiently.
    """
    logger.info(f"Fetching dataset: {dataset_name}, split: {split}")
    try:
        ds = load_dataset(dataset_name, split=split, streaming=True)
        for record in ds:
            yield record
    except Exception as e:
        logger.error(f"Failed to fetch dataset: {e}")
        raise

def parse_jsonl_file(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """Parse a JSONL file and yield records."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSONL file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON on line {line_num}: {e}")
                raise

def save_to_jsonl(data: List[Dict[str, Any]], file_path: str):
    """Save a list of records to a JSONL file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        for record in data:
            f.write(json.dumps(record) + '\n')
    logger.info(f"Saved {len(data)} records to {file_path}")

def load_from_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load records from a JSONL file into a list."""
    records = []
    for record in parse_jsonl_file(file_path):
        records.append(record)
    return records

def get_dataset_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate basic statistics about the dataset."""
    if not records:
        return {"count": 0}
    
    stats = {
        "count": len(records),
        "domains": {},
        "roles": {},
        "outcomes": {}
    }
    
    for record in records:
        domain = record.get('domain', 'unknown')
        role = record.get('role', 'unknown')
        outcome = record.get('outcome', 'unknown')
        
        stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
        stats["roles"][role] = stats["roles"].get(role, 0) + 1
        stats["outcomes"][outcome] = stats["outcomes"].get(outcome, 0) + 1
        
    return stats

def run_data_loader_pipeline(input_source: str, schema_path: str = "contracts/dataset.schema.yaml", output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Main pipeline function to load, validate, and optionally save data.
    
    Args:
        input_source: Path to JSONL file or HuggingFace dataset name.
        schema_path: Path to the schema YAML file.
        output_path: Optional path to save validated data.
        
    Returns:
        List of validated records.
    """
    ensure_dirs()
    schema = load_schema(schema_path)
    validated_records = []
    
    logger.info(f"Starting data loader pipeline with schema: {schema_path}")
    
    # Determine input type
    if input_source.endswith('.jsonl'):
        logger.info(f"Parsing JSONL file: {input_source}")
        generator = parse_jsonl_file(input_source)
    else:
        logger.info(f"Fetching from HuggingFace: {input_source}")
        generator = fetch_gatemem(dataset_name=input_source)
    
    # Process records
    for idx, record in enumerate(generator):
        try:
            validate_fields(record, schema)
            validated_records.append(record)
            if (idx + 1) % 1000 == 0:
                logger.info(f"Processed {idx + 1} records...")
        except (ValueError, TypeError) as e:
            logger.error(f"Validation failed for record at index {idx}: {e}")
            raise
    
    logger.info(f"Successfully validated {len(validated_records)} records.")
    
    if output_path:
        save_to_jsonl(validated_records, output_path)
        
    return validated_records

def main():
    """Entry point for the data loader script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GateMem Data Loader")
    parser.add_argument('--input', type=str, default="llmXive/gatemem", help="Input source (HuggingFace dataset name or JSONL path)")
    parser.add_argument('--schema', type=str, default="contracts/dataset.schema.yaml", help="Path to schema file")
    parser.add_argument('--output', type=str, default="data/processed/validated_data.jsonl", help="Output path for validated data")
    
    args = parser.parse_args()
    
    try:
        run_data_loader_pipeline(args.input, args.schema, args.output)
        logger.info("Data loader pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Data loader pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()