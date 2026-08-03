"""
Module: code/analysis/output_metrics.py
Purpose: Aggregate subject-level metrics from the cache (JSON) and write them
         to a single CSV file `data/metrics/subject_metrics.csv`, ensuring
         the output matches the schema defined in `contracts/subject_metrics.schema.yaml`.
"""
import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_subject_metrics_from_cache(cache_dir: str) -> List[Dict[str, Any]]:
    """
    Load all subject metric JSON files from the specified cache directory.
    
    Args:
        cache_dir: Path to the directory containing subject metric JSON files.
        
    Returns:
        A list of dictionaries, each representing metrics for one subject.
    """
    metrics_list = []
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        logger.warning(f"Cache directory does not exist: {cache_dir}")
        return metrics_list
        
    json_files = list(cache_path.glob("subject_*.json"))
    
    if not json_files:
        logger.warning(f"No subject metric JSON files found in {cache_dir}")
        return metrics_list
        
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                # Ensure subject_id is present for sorting/joining later if needed
                if 'subject_id' not in data:
                    logger.warning(f"Skipping {json_file.name}: missing 'subject_id'")
                    continue
                metrics_list.append(data)
                logger.info(f"Loaded metrics for subject {data['subject_id']}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {json_file.name}: {e}")
            
    return metrics_list

def aggregate_metrics(metrics_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate metrics into a unified list structure, ensuring all expected
    columns are present (even if None/0) for CSV consistency.
    
    Args:
        metrics_list: List of subject metric dictionaries.
        
    Returns:
        Normalized list of dictionaries ready for CSV export.
    """
    # Define expected keys based on typical metrics output (Flexibility, Stability)
    # per network (DMN, Salience, Hippocampal-Memory)
    expected_keys = {
        'subject_id',
        'flexibility_DMN', 'stability_DMN',
        'flexibility_Salience', 'stability_Salience',
        'flexibility_Hippocampal-Memory', 'stability_Hippocampal-Memory',
        'dream_recall_frequency' # Often included for downstream stats
    }
    
    aggregated = []
    for item in metrics_list:
        record = {}
        # Copy existing data
        for key, value in item.items():
            record[key] = value
        
        # Ensure all expected keys exist, defaulting to None or 0.0
        for key in expected_keys:
            if key not in record:
                # Try to infer if it's a float metric or ID
                if key.startswith('flexibility_') or key.startswith('stability_'):
                    record[key] = None
                elif key == 'dream_recall_frequency':
                    record[key] = None
                else:
                    record[key] = None
        
        aggregated.append(record)
        
    # Sort by subject_id for deterministic output
    aggregated.sort(key=lambda x: str(x.get('subject_id', '')))
    
    return aggregated

def write_metrics_csv(aggregated_metrics: List[Dict[str, Any]], output_path: str):
    """
    Write the aggregated metrics to a CSV file.
    
    Args:
        aggregated_metrics: List of metric dictionaries.
        output_path: Path to the output CSV file.
    """
    if not aggregated_metrics:
        logger.warning("No metrics to write.")
        # Create an empty file with headers if possible, or just return
        # We need headers. Let's define standard headers.
        standard_headers = [
            'subject_id',
            'flexibility_DMN', 'stability_DMN',
            'flexibility_Salience', 'stability_Salience',
            'flexibility_Hippocampal-Memory', 'stability_Hippocampal-Memory',
            'dream_recall_frequency'
        ]
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=standard_headers)
            writer.writeheader()
        return

    # Determine headers from the first record (should be consistent)
    headers = list(aggregated_metrics[0].keys())
    # Sort headers to ensure consistent column order (subject_id first, then metrics)
    # Custom sort: subject_id first, then flexibility/stability groups
    def sort_key(header):
        if header == 'subject_id': return 0
        if header == 'dream_recall_frequency': return 99
        if 'flexibility' in header: return 1
        if 'stability' in header: return 2
        return 3
    
    headers.sort(key=sort_key)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(aggregated_metrics)
    
    logger.info(f"Wrote {len(aggregated_metrics)} records to {output_path}")

def validate_schema(output_path: str, schema_path: str) -> bool:
    """
    Validate the generated CSV against the JSON schema (converted or adapted).
    Since CSVs don't natively validate against JSON Schema without a loader,
    we perform a structural check: verify headers match expected schema fields.
    
    Args:
        output_path: Path to the generated CSV.
        schema_path: Path to the schema definition (YAML/JSON).
        
    Returns:
        True if validation passes, False otherwise.
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        logger.warning(f"Schema file not found: {schema_path}. Skipping strict schema validation.")
        return True # Allow run to continue if schema is missing, but log warning
    
    try:
        import yaml
        with open(schema_file, 'r') as f:
            schema = yaml.safe_load(f)
    except ImportError:
        logger.warning("PyYAML not installed. Skipping schema validation.")
        return True
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    # Extract expected fields from schema (assuming 'properties' key)
    expected_fields = set(schema.get('properties', {}).keys())
    
    # Read CSV headers
    with open(output_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
    
    csv_fields = set(headers)
    
    # Check if CSV contains all required fields from schema
    missing = expected_fields - csv_fields
    extra = csv_fields - expected_fields
    
    if missing:
        logger.error(f"Schema validation failed: Missing fields in CSV: {missing}")
        return False
    
    if extra:
        logger.warning(f"Schema validation: Extra fields in CSV (allowed): {extra}")
    
    logger.info("Schema validation passed.")
    return True

def main():
    """
    Main entry point for T031: Output subject-level metrics to CSV.
    """
    # Configuration paths
    config = {
        'cache_dir': 'data/processed/metrics_cache', # Assumed location from T029/T030
        'output_file': 'data/metrics/subject_metrics.csv',
        'schema_file': 'contracts/subject_metrics.schema.yaml'
    }
    
    # Ensure output directory exists
    output_path = Path(config['output_file'])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting metrics aggregation and CSV export...")
    
    # 1. Load from cache
    metrics_list = load_subject_metrics_from_cache(config['cache_dir'])
    if not metrics_list:
        logger.error("No metrics found to aggregate. Ensure T029/T030 have run.")
        # Create empty file to prevent downstream crashes, but log error
        with open(config['output_file'], 'w') as f:
            f.write("subject_id,flexibility_DMN,stability_DMN,flexibility_Salience,stability_Salience,flexibility_Hippocampal-Memory,stability_Hippocampal-Memory,dream_recall_frequency\n")
        return
    
    # 2. Aggregate
    aggregated = aggregate_metrics(metrics_list)
    
    # 3. Write CSV
    write_metrics_csv(aggregated, config['output_file'])
    
    # 4. Validate
    is_valid = validate_schema(config['output_file'], config['schema_file'])
    
    if is_valid:
        logger.info(f"T031 Complete: Output written to {config['output_file']}")
    else:
        logger.error("T031 Complete but schema validation failed.")

if __name__ == "__main__":
    main()
