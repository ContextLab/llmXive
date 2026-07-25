import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from code.src.simulation.schema import validate_simulation_run, get_results_schema, SchemaError

logger = logging.getLogger(__name__)

def load_simulation_results(file_path: Path) -> List[Dict[str, Any]]:
    """Load simulation results from a JSON file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'results' in data:
        return data['results']
    else:
        raise ValueError(f"Unexpected data format in {file_path}")

def save_simulation_result(result: Dict[str, Any], output_path: Path) -> None:
    """
    Save a single simulation result to a JSON file.
    
    Validates the result against the schema defined in T029a before writing.
    If validation fails, raises a ValueError and does NOT write the file.
    
    Args:
        result: The simulation result dictionary.
        output_path: The path to write the JSON file.
    
    Raises:
        ValueError: If the result fails schema validation.
        SchemaError: If the schema itself is invalid or missing.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate against schema
    schema = get_results_schema()
    try:
        validate_simulation_run(result, schema)
    except SchemaError as e:
        logger.error(f"Schema validation failed for result {result.get('network_id', 'unknown')}: {e}")
        raise ValueError(f"Invalid simulation result: {e}")
    
    # Write to disk
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved simulation result to {output_path}")

def save_batch_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save a batch of simulation results to a JSON file.
    
    Validates each result against the schema. If ANY result fails validation,
    the entire batch is rejected and no file is written.
    
    Args:
        results: List of simulation result dictionaries.
        output_path: The path to write the JSON file.
    
    Raises:
        ValueError: If any result fails schema validation.
    """
    if not results:
        logger.warning("No results to save.")
        return

    schema = get_results_schema()
    invalid_count = 0
    
    for i, result in enumerate(results):
        try:
            validate_simulation_run(result, schema)
        except SchemaError as e:
            logger.error(f"Schema validation failed for result {i} (ID: {result.get('network_id', 'unknown')}): {e}")
            invalid_count += 1

    if invalid_count > 0:
        raise ValueError(f"Found {invalid_count} invalid results. Batch write aborted.")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to disk
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {len(results)} simulation results to {output_path}")

def main() -> None:
    """
    CLI entry point for serialization tasks.
    Typically invoked by run_simulation.py to save results immediately after generation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Serialize simulation results.")
    parser.add_argument("--input", required=True, help="Path to input results (JSON list or single object).")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    parser.add_argument("--append", action="store_true", help="Append to existing file (requires list format).")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    results = data if isinstance(data, list) else [data]
    
    try:
        if args.append and output_path.exists():
            with open(output_path, 'r') as f:
                existing = json.load(f)
            if not isinstance(existing, list):
                raise ValueError("Append mode requires existing file to be a JSON list.")
            existing.extend(results)
            results = existing
        
        save_batch_results(results, output_path)
        print(f"Successfully saved {len(results)} results to {output_path}")
    except (ValueError, SchemaError) as e:
        print(f"Serialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
