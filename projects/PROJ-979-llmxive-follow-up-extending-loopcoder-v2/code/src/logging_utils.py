"""
Logging and result serialization utilities for the llmXive pipeline.
Provides robust CSV/JSON serialization for entropy and convergence results.
"""
import csv
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging if not already configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dir(output_path: str) -> Path:
    """
    Ensures the directory for the given output path exists.
    
    Args:
        output_path: Full path to the output file.
        
    Returns:
        The Path object for the directory.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.parent

def save_results_to_csv(data: List[Dict[str, Any]], output_path: str, fieldnames: List[str]) -> None:
    """
    Saves a list of dictionaries to a CSV file.
    
    Args:
        data: List of result dictionaries.
        output_path: Path to the output CSV file.
        fieldnames: List of column names in order.
    """
    ensure_output_dir(output_path)
    
    if not data:
        logger.warning(f"No data to write to {output_path}. Creating empty file.")
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Successfully saved {len(data)} records to {output_path}")

def save_results_to_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Saves a list of dictionaries to a JSON file.
    
    Args:
        data: List of result dictionaries.
        output_path: Path to the output JSON file.
    """
    ensure_output_dir(output_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Successfully saved {len(data)} records to {output_path}")

def serialize_entropy_results(entropy_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Serializes entropy extraction results to CSV.
    
    Args:
        entropy_data: List of dictionaries containing entropy results.
                      Expected keys: task_id, entropy, cluster_count, sample_count, strata.
        output_path: Path to the output CSV file.
    """
    fieldnames = ['task_id', 'entropy', 'cluster_count', 'sample_count', 'strata', 'status']
    save_results_to_csv(entropy_data, output_path, fieldnames)

def serialize_convergence_results(convergence_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Serializes convergence trajectory results to CSV.
    
    Args:
        convergence_data: List of dictionaries containing convergence results.
                          Expected keys: task_id, k, converged, steps_to_converge, solution_code, strata.
        output_path: Path to the output CSV file.
    """
    fieldnames = ['task_id', 'k', 'converged', 'steps_to_converge', 'solution_code', 'strata', 'execution_status']
    save_results_to_csv(convergence_data, output_path, fieldnames)

def log_exclusions(exclusion_log: List[Dict[str, Any]], output_path: str) -> None:
    """
    Logs exclusion events (e.g., undefined entropy, execution failures) to JSON.
    
    Args:
        exclusion_log: List of exclusion event dictionaries.
        output_path: Path to the exclusion log JSON file.
    """
    save_results_to_json(exclusion_log, output_path)
    logger.info(f"Logged {len(exclusion_log)} exclusion events to {output_path}")
