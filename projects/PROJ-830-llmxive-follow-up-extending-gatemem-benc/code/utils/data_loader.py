import os
import json
import logging
from typing import Dict, List, Any, Optional, Generator
import pandas as pd
from datasets import load_dataset
from pathlib import Path
import yaml

from logging_config import setup_logging

logger = setup_logging(__name__)

def ensure_dirs():
    """Ensure required directories exist."""
    dirs = ["data/raw", "data/processed", "data/samples", "logs"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_fields(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> None:
    """
    Validate that all records contain required fields defined in the schema.
    Raises ValueError if any required field is missing.
    """
    required_fields = schema.get("required", [])
    missing_fields = set()

    for i, record in enumerate(data):
        for field in required_fields:
            if field not in record or record[field] is None:
                missing_fields.add(field)
        
        # Optimization: if we found all required fields missing in a sample, break early?
        # No, we need to check all or at least report all missing types.

    if missing_fields:
        raise ValueError(f"Missing required fields in dataset: {missing_fields}. "
                       f"Expected fields per schema: {required_fields}")

def fetch_gatemem(dataset_name: str = "llmXive/GateMem", split: str = "train", streaming: bool = False) -> List[Dict[str, Any]]:
    """
    Fetch the GateMem dataset from HuggingFace.
    If streaming is True, returns a generator.
    Otherwise, loads into memory (chunked if large).
    """
    logger.info(f"Fetching dataset: {dataset_name}, split: {split}")
    
    try:
        ds = load_dataset(dataset_name, split=split, streaming=streaming)
        if streaming:
            return list(ds) # For simplicity in this context, convert to list. 
                            # In production, iterate directly to save memory.
        else:
            return list(ds)
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_name}: {e}")
        raise

def parse_jsonl_file(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """Parse a JSONL file line by line."""
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def save_to_jsonl(data: List[Dict[str, Any]], output_path: str) -> None:
    """Save a list of dicts to a JSONL file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")

def load_from_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load all records from a JSONL file."""
    return list(parse_jsonl_file(file_path))

def get_dataset_statistics(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate basic statistics about the dataset."""
    if not data:
        return {"count": 0}
    
    domains = set(d.get("domain", "unknown") for d in data)
    roles = set(d.get("role", "unknown") for d in data)
    
    return {
        "count": len(data),
        "domains": list(domains),
        "roles": list(roles)
    }

def run_data_loader_pipeline(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Main entry point for data loading and validation.
    1. Fetch data
    2. Validate fields against schema
    3. Return data
    """
    schema_path = config.get("schema_path", "contracts/dataset.schema.yaml")
    dataset_name = config.get("dataset_name", "llmXive/GateMem")
    
    schema = load_schema(schema_path)
    data = fetch_gatemem(dataset_name)
    
    logger.info(f"Validating {len(data)} records against schema...")
    validate_fields(data, schema)
    logger.info("Validation passed.")
    
    return data

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="llmXive/GateMem")
    parser.add_argument("--schema", type=str, default="contracts/dataset.schema.yaml")
    args = parser.parse_args()
    
    config = {
        "dataset_name": args.dataset,
        "schema_path": args.schema
    }
    
    try:
        data = run_data_loader_pipeline(config)
        print(f"Successfully loaded and validated {len(data)} records.")
    except ValueError as e:
        print(f"Validation Error: {e}")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()
