"""
Data loader for GateMem dataset with schema validation.
"""
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

def ensure_dirs(base_path: str = "data") -> None:
    """Ensure required directories exist."""
    dirs = [
        os.path.join(base_path, "raw"),
        os.path.join(base_path, "processed"),
        os.path.join(base_path, "samples"),
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist under {base_path}")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def validate_fields(record: Dict[str, Any], schema: Dict[str, Any], source: str = "data") -> bool:
    """
    Validate that a record contains all required fields from the schema.
    Raises ValueError if any required field is missing.
    """
    required_fields = schema.get("required", [])
    missing_fields = [field for field in required_fields if field not in record]

    if missing_fields:
        error_msg = (
            f"Validation failed in {source}: Missing required fields: {missing_fields}. "
            f"Record keys found: {list(record.keys())}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.debug(f"Validation passed for record in {source}")
    return True

def fetch_gatemem(dataset_name: str = "llmXive/GateMem", split: str = "train") -> Generator[Dict[str, Any], None, None]:
    """
    Fetch GateMem dataset from HuggingFace.
    Returns a generator to handle large datasets efficiently.
    """
    logger.info(f"Fetching dataset: {dataset_name} (split={split})")
    try:
        ds = load_dataset(dataset_name, split=split, streaming=True)
        for item in ds:
            yield item
    except Exception as e:
        logger.error(f"Failed to fetch dataset from HuggingFace: {e}")
        raise RuntimeError(f"Could not fetch dataset '{dataset_name}'. Verify internet connection and dataset availability.") from e

def parse_jsonl_file(file_path: str) -> Generator[Dict[str, Any], None, None]:
    """Parse a JSONL file line by line."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSONL file not found: {file_path}")
    
    logger.info(f"Parsing JSONL file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping malformed JSON at line {line_num}: {e}")
                continue

def save_to_jsonl(data: List[Dict[str, Any]], output_path: str) -> None:
    """Save a list of records to a JSONL file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for record in data:
            f.write(json.dumps(record) + "\n")
    logger.info(f"Saved {len(data)} records to {output_path}")

def load_from_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """Load all records from a JSONL file."""
    records = []
    for record in parse_jsonl_file(file_path):
        records.append(record)
    return records

def get_dataset_statistics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate basic statistics for a list of records."""
    if not records:
        return {"count": 0}
    
    stats = {
        "count": len(records),
        "domains": {},
        "roles": {},
        "has_leak_target": 0,
    }
    
    for record in records:
        domain = record.get("domain", "unknown")
        stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
        
        role = record.get("role", "unknown")
        stats["roles"][role] = stats["roles"].get(role, 0) + 1
        
        if "leak-target" in record:
            stats["has_leak_target"] += 1
    
    return stats

def run_data_loader_pipeline(
    schema_path: str = "contracts/dataset.schema.yaml",
    source_type: str = "huggingface",
    source_arg: Optional[str] = None,
    output_path: Optional[str] = None,
    validate: bool = True
) -> List[Dict[str, Any]]:
    """
    Main pipeline to load, validate, and optionally save data.
    
    Args:
        schema_path: Path to the YAML schema file.
        source_type: 'huggingface' or 'jsonl'.
        source_arg: Dataset name (for HF) or file path (for JSONL).
        output_path: If provided, save validated records here.
        validate: If True, enforce schema validation.
    
    Returns:
        List of validated records.
    """
    ensure_dirs()
    schema = load_schema(schema_path)
    
    logger.info("Starting data loading pipeline")
    records = []
    
    if source_type == "huggingface":
        dataset_name = source_arg or "llmXive/GateMem"
        gen = fetch_gatemem(dataset_name)
    elif source_type == "jsonl":
        if not source_arg:
            raise ValueError("source_arg (file path) required for JSONL mode")
        gen = parse_jsonl_file(source_arg)
    else:
        raise ValueError(f"Unsupported source_type: {source_type}")
    
    for i, record in enumerate(gen):
        if validate:
            try:
                validate_fields(record, schema, source=source_type)
            except ValueError as e:
                logger.error(f"Skipping invalid record at index {i}: {e}")
                continue
        records.append(record)
        
        if (i + 1) % 1000 == 0:
            logger.info(f"Processed {i + 1} records...")
    
    if output_path:
        save_to_jsonl(records, output_path)
    
    logger.info(f"Pipeline complete. Loaded {len(records)} valid records.")
    return records

def main():
    """CLI entry point for data loader."""
    import argparse
    
    parser = argparse.ArgumentParser(description="GateMem Data Loader")
    parser.add_argument("--schema", default="contracts/dataset.schema.yaml", help="Path to schema YAML")
    parser.add_argument("--source", choices=["huggingface", "jsonl"], default="huggingface", help="Data source type")
    parser.add_argument("--arg", type=str, help="Dataset name or file path")
    parser.add_argument("--output", type=str, help="Output JSONL path")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    
    args = parser.parse_args()
    
    records = run_data_loader_pipeline(
        schema_path=args.schema,
        source_type=args.source,
        source_arg=args.arg,
        output_path=args.output,
        validate=not args.no_validate
    )
    
    stats = get_dataset_statistics(records)
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()