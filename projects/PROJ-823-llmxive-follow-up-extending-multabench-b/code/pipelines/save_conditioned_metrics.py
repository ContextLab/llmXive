import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_error, log_debug
from analysis.evaluate_metrics import load_dataset_list, evaluate_dataset, save_metrics_to_json

logger = get_logger(__name__)

def generate_run_id() -> str:
    """Generate a deterministic run ID based on current timestamp and a hash."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_part = hashlib.sha256(timestamp.encode()).hexdigest()[:8]
    return f"run_{timestamp}_{random_part}"

def load_projected_metrics(dataset_id: str, run_id: str) -> Optional[Dict[str, Any]]:
    """
    Load metrics computed for a specific dataset and run.
    Assumes T027 (evaluation logic) has already written metrics to data/artifacts/
    or a specific location defined by the project convention.
    """
    # Expected path based on T027 implementation pattern:
    # data/artifacts/metrics_{dataset_id}_{run_id}.json
    metrics_path = Path("data/artifacts") / f"metrics_{dataset_id}_{run_id}.json"
    
    if not metrics_path.exists():
        log_warning(f"Metrics file not found for {dataset_id}: {metrics_path}")
        return None
    
    try:
        with open(metrics_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse metrics file for {dataset_id}: {e}")
        return None

def aggregate_conditioned_metrics(datasets: List[Dict[str, str]], run_id: str) -> List[Dict[str, Any]]:
    """
    Aggregate metrics from all processed datasets into a single list.
    Each entry includes the dataset_id, run_id, and the computed metrics.
    """
    aggregated_results = []
    
    for dataset_info in datasets:
        dataset_id = dataset_info.get('dataset_id')
        if not dataset_id:
            log_warning("Skipping dataset entry without 'dataset_id'")
            continue
        
        metrics = load_projected_metrics(dataset_id, run_id)
        if metrics:
            # Ensure run_id is linked in the result
            metrics['run_id'] = run_id
            metrics['dataset_id'] = dataset_id
            aggregated_results.append(metrics)
            log_info(f"Aggregated metrics for dataset: {dataset_id}")
        else:
            log_warning(f"No metrics found for dataset {dataset_id}, skipping aggregation.")
    
    return aggregated_results

def save_aggregated_metrics(results: List[Dict[str, Any]], run_id: str) -> str:
    """
    Save the aggregated metrics to the required output file:
    data/artifacts/metrics_conditioned_{run_id}.json
    """
    output_dir = Path("data/artifacts")
    ensure_directories([output_dir])
    
    output_path = output_dir / f"metrics_conditioned_{run_id}.json"
    
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        log_info(f"Successfully saved conditioned metrics to {output_path}")
        return str(output_path)
    except IOError as e:
        log_error(f"Failed to write aggregated metrics to {output_path}: {e}")
        raise

def main():
    """
    Main entry point for T028: Store results in data/artifacts/metrics_conditioned_{run_id}.json
    """
    log_info("Starting T028: Aggregating and storing conditioned metrics...")
    
    # Generate or retrieve run_id. 
    # In a real pipeline, this might be passed as an argument or derived from previous steps.
    # For this script, we generate a new one or try to infer from existing files if needed.
    # Here we generate a fresh one to ensure unique artifact naming per run.
    run_id = generate_run_id()
    log_info(f"Using run_id: {run_id}")
    
    # Load list of datasets to process
    datasets = load_dataset_list()
    if not datasets:
        log_error("No datasets found to process. Exiting.")
        sys.exit(1)
    
    log_info(f"Found {len(datasets)} datasets to aggregate metrics for.")
    
    # Aggregate metrics from individual dataset evaluation results
    aggregated_metrics = aggregate_conditioned_metrics(datasets, run_id)
    
    if not aggregated_metrics:
        log_warning("No metrics were aggregated. Output file will be empty.")
    
    # Save to the required path
    output_path = save_aggregated_metrics(aggregated_metrics, run_id)
    
    log_info(f"T028 completed. Output written to: {output_path}")
    return output_path

if __name__ == "__main__":
    main()