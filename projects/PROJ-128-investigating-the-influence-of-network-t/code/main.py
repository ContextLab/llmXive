import os
import sys
import json
import traceback
import numpy as np
import pandas as pd
from pathlib import Path
from preprocess.structural import run_structural_pipeline
from preprocess.functional import run_functional_pipeline
from config import get_config_dict
from utils.cpu_optimization import (
    validate_no_gpu_acceleration, 
    optimize_memory_usage, 
    set_random_seed
)

def get_exclusion_log_path() -> Path:
    """Get path to exclusion log file."""
    config = get_config_dict()
    return Path(config['paths']['logs_dir']) / 'exclusion_log.json'

def load_exclusion_log() -> dict:
    """Load exclusion log from file."""
    path = get_exclusion_log_path()
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {'excluded_subjects': [], 'reasons': {}}

def save_exclusion_log(log_data: dict) -> None:
    """Save exclusion log to file."""
    path = get_exclusion_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(log_data, f, indent=2)

def log_subject_exclusion(subject_id: str, reason: str) -> None:
    """Log a subject exclusion to the exclusion log."""
    log_data = load_exclusion_log()
    log_data['excluded_subjects'].append(subject_id)
    log_data['reasons'][subject_id] = reason
    save_exclusion_log(log_data)

def process_subject(subject_id: str, config: dict) -> dict:
    """
    Process a single subject: compute structural and dynamic metrics.
    
    Args:
        subject_id: Subject identifier
        config: Configuration dictionary
        
    Returns:
        Dictionary containing computed metrics
    """
    try:
        # Validate CPU-only execution
        validate_no_gpu_acceleration()
        
        # Run structural pipeline
        structural_metrics = run_structural_pipeline(subject_id, config)
        
        # Run functional pipeline
        dynamic_metrics = run_functional_pipeline(subject_id, config)
        
        # Combine results
        result = {
            'subject_id': subject_id,
            'structural': structural_metrics,
            'dynamic': dynamic_metrics
        }
        
        return result
        
    except Exception as e:
        log_subject_exclusion(subject_id, str(e))
        raise

def aggregate_metrics_to_csv(results: list) -> None:
    """
    Aggregate subject metrics into CSV files.
    
    Args:
        results: List of dictionaries containing subject metrics
    """
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed_dir'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    structural_data = []
    dynamic_data = []
    
    for result in results:
        subject_id = result['subject_id']
        
        # Flatten structural metrics
        for metric, value in result['structural'].items():
            structural_data.append({
                'subject_id': subject_id,
                'metric': metric,
                'value': value
            })
        
        # Flatten dynamic metrics
        for metric, value in result['dynamic'].items():
            dynamic_data.append({
                'subject_id': subject_id,
                'metric': metric,
                'value': value
            })
    
    # Create DataFrames and optimize memory
    df_structural = pd.DataFrame(structural_data)
    df_dynamic = pd.DataFrame(dynamic_data)
    
    df_structural = optimize_memory_usage(df_structural)
    df_dynamic = optimize_memory_usage(df_dynamic)
    
    # Save to CSV
    df_structural.to_csv(processed_dir / 'structural_metrics.csv', index=False)
    df_dynamic.to_csv(processed_dir / 'dynamic_metrics.csv', index=False)

def main() -> None:
    """Main entry point for the pipeline."""
    # Set random seed for reproducibility
    set_random_seed(42)
    
    # Validate CPU-only execution
    validate_no_gpu_acceleration()
    
    config = get_config_dict()
    
    # Get subject list (in a real implementation, this would come from data loader)
    # For now, we assume subjects are processed individually and aggregated
    # This is a placeholder for the actual batch processing logic
    
    print("Starting pipeline execution...")
    print("CPU-only mode validated.")
    
    # In a real implementation, we would iterate over subjects
    # and call process_subject for each one
    
    # For this task, we ensure the infrastructure is in place
    # The actual batch processing happens when real data is available
    print("Pipeline infrastructure ready for CPU-only execution.")

if __name__ == '__main__':
    main()
