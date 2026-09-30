"""
Validates the generated graph_metrics.csv against the schema defined in
specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/graph_metrics.schema.yaml.
"""
import os
import csv
import json
import jsonschema
import logging
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCHEMA_PATH = Path("specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/graph_metrics.schema.yaml")
DATA_PATH = Path("data/processed/graph_metrics.csv")

def load_schema(path: Path) -> Dict[str, Any]:
    """Load the YAML schema file."""
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found at {path}")
    # Since jsonschema expects JSON or a dict, and we have a YAML file,
    # we need to parse it. We'll use a simple manual parse or assume PyYAML is available.
    # Given requirements.txt includes common libs, we assume yaml is available.
    try:
        import yaml
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback if yaml is not installed but json is (unlikely for this project)
        # Or raise a clear error
        raise ImportError("PyYAML is required to load .yaml schema files. Please install it.")

def load_csv_as_records(path: Path) -> List[Dict[str, Any]]:
    """Load CSV records and convert types to match JSON schema expectations."""
    if not path.exists():
        raise FileNotFoundError(f"Data file not found at {path}")
    
    records = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            record = {
                "device_id": row["device_id"],
                "metric_name": row["metric_name"],
                "value": float(row["value"]),
                "is_finite": row["is_finite"].lower() == 'true'
            }
            records.append(record)
    return records

def validate_records(records: List[Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """Validate a list of records against the schema."""
    # jsonschema.validate checks a single instance. We need to validate the list of objects.
    # The schema defines the structure of a SINGLE object. We validate each row.
    errors = []
    for i, record in enumerate(records):
        try:
            jsonschema.validate(instance=record, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Row {i}: {e.message}")
    
    if errors:
        logger.error("Validation failed with the following errors:")
        for err in errors:
            logger.error(f"  - {err}")
        return False
    
    logger.info(f"Successfully validated {len(records)} records against the schema.")
    return True

def main():
    logger.info("Starting Graph Metrics Schema Validation...")
    
    try:
        schema = load_schema(SCHEMA_PATH)
        logger.info(f"Loaded schema from {SCHEMA_PATH}")
        
        records = load_csv_as_records(DATA_PATH)
        logger.info(f"Loaded {len(records)} records from {DATA_PATH}")
        
        if validate_records(records, schema):
            logger.info("Validation PASSED: graph_metrics.csv conforms to the schema.")
            return 0
        else:
            logger.error("Validation FAILED: graph_metrics.csv does not conform to the schema.")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
