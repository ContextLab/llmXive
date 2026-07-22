"""
save_perturbed_vectors.py

Implements T025: Save perturbed vectors and metadata to data/processed/perturbed_vectors.csv
linked by PairID and sigma.

This script is designed to be run after the perturbation sweep (T024) has generated
the perturbation results in memory or temporary storage. It aggregates the results
into a single CSV file as required by the data schema.
"""
import os
import sys
import csv
import json
import logging
import torch
import numpy as np
from typing import List, Dict, Any, Optional, Iterator, Tuple
from pathlib import Path

# Import from project modules
from config import load_config, OutputPaths, PipelineConfig
from streaming_utils import batch_iterator
from memory_monitor import get_current_memory_mb, check_memory_limit, MemoryLimitExceeded

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_perturbation_results(
    perturbation_log_path: str,
    batch_size: int = 1000
) -> Iterator[Dict[str, Any]]:
    """
    Load perturbation results from the log generated during the sweep.
    
    Expected format in perturbation_log_path (JSONL or JSON):
    - If JSONL: Each line is a JSON object with keys:
      {
        "pair_id": "string",
        "sigma": float,
        "task_type": "string",
        "vector": [list of floats],
        "validity_passed": bool,
        "input_drift_passed": bool,
        "output_validity_passed": bool
      }
    - If JSON: A list of such objects.
    
    Yields:
        Dict[str, Any]: A dictionary representing a single perturbation record.
    """
    logger.info(f"Loading perturbation results from {perturbation_log_path}")
    
    if not os.path.exists(perturbation_log_path):
        raise FileNotFoundError(f"Perturbation log not found: {perturbation_log_path}")

    try:
        with open(perturbation_log_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            
        if not content:
            logger.warning("Perturbation log is empty.")
            return

        # Try parsing as JSONL first (line by line)
        if '\n' in content:
            logger.info("Detected JSONL format.")
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    yield record
                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping invalid JSON line: {e}")
                    continue
        else:
            # Try parsing as a single JSON list
            logger.info("Detected JSON list format.")
            try:
                records = json.loads(content)
                if not isinstance(records, list):
                    raise ValueError("Expected a JSON list of records.")
                for record in records:
                    yield record
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON file: {e}")
                raise

    except Exception as e:
        logger.error(f"Error reading perturbation log: {e}")
        raise

def parse_vector(vector_data: Any) -> np.ndarray:
    """
    Convert vector data (list, tensor, or string) to a numpy array.
    
    Args:
        vector_data: The vector data in various formats.
        
    Returns:
        np.ndarray: The vector as a numpy array.
    """
    if isinstance(vector_data, torch.Tensor):
        return vector_data.detach().cpu().numpy()
    elif isinstance(vector_data, list):
        return np.array(vector_data, dtype=np.float32)
    elif isinstance(vector_data, np.ndarray):
        return vector_data
    elif isinstance(vector_data, str):
        # Assume comma-separated floats if string
        return np.array([float(x) for x in vector_data.split(',')], dtype=np.float32)
    else:
        raise TypeError(f"Unsupported vector type: {type(vector_data)}")

def validate_and_prepare_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and prepare a single record for CSV output.
    
    Ensures:
    - pair_id is present
    - sigma is a number
    - vector is a list of floats
    - validity flags are booleans
    
    Args:
        record: The raw record from the log.
        
    Returns:
        Dict[str, Any]: The validated and prepared record.
        
    Raises:
        ValueError: If the record is invalid.
    """
    required_keys = ['pair_id', 'sigma', 'vector']
    for key in required_keys:
        if key not in record:
            raise ValueError(f"Missing required key: {key}")

    pair_id = str(record['pair_id'])
    sigma = float(record['sigma'])
    
    vector = parse_vector(record['vector'])
    
    # Ensure L2 normalization (as per T015/T016 requirements for baseline, 
    # and typically expected for perturbed vectors in this context)
    norm = np.linalg.norm(vector)
    if norm > 1e-9:
        vector = vector / norm
    else:
        logger.warning(f"Zero norm vector for pair_id={pair_id}, sigma={sigma}. Keeping as is.")
    
    # Prepare validity flags with defaults
    validity_passed = bool(record.get('validity_passed', False))
    input_drift_passed = bool(record.get('input_drift_passed', False))
    output_validity_passed = bool(record.get('output_validity_passed', False))
    task_type = str(record.get('task_type', 'unknown'))

    return {
        'pair_id': pair_id,
        'sigma': sigma,
        'task_type': task_type,
        'vector': vector.tolist(), # Convert back to list for CSV
        'validity_passed': validity_passed,
        'input_drift_passed': input_drift_passed,
        'output_validity_passed': output_validity_passed,
        'vector_dimension': len(vector)
    }

def save_perturbed_vectors(
    records_iterator: Iterator[Dict[str, Any]],
    output_path: str,
    batch_size: int = 1000
) -> int:
    """
    Save perturbed vectors and metadata to a CSV file.
    
    Args:
        records_iterator: Iterator yielding validated records.
        output_path: Path to the output CSV file.
        batch_size: Number of records to process in a batch (for memory efficiency).
        
    Returns:
        int: The number of records saved.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Created output directory: {output_dir}")

    fieldnames = [
        'pair_id', 'sigma', 'task_type', 
        'validity_passed', 'input_drift_passed', 'output_validity_passed',
        'vector_dimension', 'vector'
    ]
    
    count = 0
    batch = []
    
    logger.info(f"Starting to save perturbed vectors to {output_path}")
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records_iterator:
                # Memory check
                if count % batch_size == 0 and count > 0:
                    current_mem = get_current_memory_mb()
                    # Assuming a 7GB limit as per T008b, but we check periodically
                    # If this script is run in a constrained environment, we might need to adjust
                    if current_mem > 6000: # 6GB safety buffer
                        logger.warning(f"Memory usage high: {current_mem:.2f} MB. Flushing batch.")
                
                prepared = validate_and_prepare_record(record)
                batch.append(prepared)
                
                if len(batch) >= batch_size:
                    writer.writerows(batch)
                    count += len(batch)
                    logger.info(f"Saved batch of {len(batch)} records. Total: {count}")
                    batch = []
                    
                    # Optional: Check memory limit explicitly
                    try:
                        check_memory_limit(limit_mb=7000)
                    except MemoryLimitExceeded:
                        logger.error("Memory limit exceeded during save.")
                        raise

            # Write remaining records
            if batch:
                writer.writerows(batch)
                count += len(batch)
                logger.info(f"Saved final batch of {len(batch)} records. Total: {count}")
                
    except Exception as e:
        logger.error(f"Error saving to CSV: {e}")
        raise
        
    logger.info(f"Successfully saved {count} perturbed vector records to {output_path}")
    return count

def main():
    """
    Main entry point for saving perturbed vectors.
    
    Usage:
        python code/save_perturbed_vectors.py [--config <path>] [--log <path>] [--output <path>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Save perturbed vectors to CSV")
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--log', type=str, help='Path to perturbation log (overrides config)')
    parser.add_argument('--output', type=str, help='Path to output CSV (overrides config)')
    args = parser.parse_args()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        # Fallback to defaults if config is missing, but warn
        logger.warning("Using default paths. Ensure perturbation_log and output paths are set.")
        from dataclasses import dataclass
        @dataclass
        class DefaultOutputPaths:
            perturbation_log: str = "data/processed/perturbation_sweep_log.jsonl"
            perturbed_vectors_csv: str = "data/processed/perturbed_vectors.csv"
        config = type('Config', (), {'output': DefaultOutputPaths()})()

    perturbation_log_path = args.log or config.output.perturbation_log
    output_path = args.output or config.output.perturbed_vectors_csv
    
    logger.info(f"Perturbation log path: {perturbation_log_path}")
    logger.info(f"Output CSV path: {output_path}")
    
    # Load and process records
    records = load_perturbation_results(perturbation_log_path)
    
    # Save to CSV
    count = save_perturbed_vectors(records, output_path)
    
    logger.info(f"Pipeline complete. {count} records saved.")

if __name__ == "__main__":
    main()
