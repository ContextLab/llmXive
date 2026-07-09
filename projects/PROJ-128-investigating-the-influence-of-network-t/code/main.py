import os
import sys
import json
import traceback
import numpy as np
import pandas as pd
from pathlib import Path
from config import get_config_dict, ensure_directories
from preprocess.structural import process_subject_structural_metrics
from preprocess.functional import run_functional_pipeline
from typing import Dict, List, Optional, Any, Tuple

def get_exclusion_log_path() -> Path:
    """Return the path to the exclusion log JSON file."""
    config = get_config_dict()
    log_dir = Path(config['paths']['logs'])
    ensure_directories()
    return log_dir / 'exclusion_log.json'

def load_exclusion_log() -> Dict[str, Any]:
    """
    Load the exclusion log from disk.
    Returns an empty dict if the file does not exist or is invalid.
    """
    path = get_exclusion_log_path()
    if not path.exists():
        return {"excluded_subjects": [], "summary": {}}
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            # Ensure structure integrity
            if "excluded_subjects" not in data:
                data["excluded_subjects"] = []
            if "summary" not in data:
                data["summary"] = {}
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load exclusion log at {path}: {e}. Starting fresh.")
        return {"excluded_subjects": [], "summary": {}}

def save_exclusion_log(data: Dict[str, Any]) -> None:
    """
    Save the exclusion log to disk.
    """
    path = get_exclusion_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def log_subject_exclusion(subject_id: str, reason: str, details: Optional[Dict] = None) -> None:
    """
    Append a subject exclusion entry to the exclusion log.
    
    Args:
        subject_id: The unique identifier of the subject.
        reason: A short string describing the exclusion reason (e.g., 'sparsity', 'convergence_failure').
        details: Optional dict with additional context (e.g., computed sparsity value).
    """
    log_data = load_exclusion_log()
    
    entry = {
        "subject_id": subject_id,
        "reason": reason,
        "timestamp": pd.Timestamp.now().isoformat(),
        "details": details or {}
    }
    
    log_data["excluded_subjects"].append(entry)
    
    # Update summary counts
    summary = log_data["summary"]
    reason_key = f"count_{reason}"
    summary[reason_key] = summary.get(reason_key, 0) + 1
    summary["total_excluded"] = summary.get("total_excluded", 0) + 1
    
    save_exclusion_log(log_data)
    print(f"Logged exclusion for subject {subject_id}: {reason}")

def process_subject(subject_id: str, structural_data: Optional[np.ndarray] = None, 
                    functional_data: Optional[np.ndarray] = None) -> Tuple[Optional[Dict], Optional[Dict]]:
    """
    Process a single subject to extract structural and dynamic metrics.
    Handles exclusion logic for sparsity and convergence failures.
    
    Returns:
        Tuple of (structural_metrics_dict, dynamic_metrics_dict) or (None, None) if excluded.
    """
    config = get_config_dict()
    sparsity_threshold = config['hyperparameters']['sparsity_threshold']
    
    # --- Structural Processing ---
    struct_metrics = None
    try:
        # If structural_data is None, we might need to load it here depending on pipeline design.
        # For this implementation, we assume the caller provides data or the function handles internal loading.
        # Assuming process_subject_structural_metrics handles the core logic and raises on sparsity.
        struct_metrics = process_subject_structural_metrics(subject_id, structural_data)
        
        # Check for sparsity post-calculation if not caught internally
        if struct_metrics and struct_metrics.get('sparsity', 0) > sparsity_threshold:
            raise ValueError(f"Sparsity {struct_metrics['sparsity']:.4f} exceeds threshold {sparsity_threshold}")
            
    except Exception as e:
        error_msg = str(e)
        reason = "structural_error"
        if "sparsity" in error_msg.lower():
            reason = "sparsity"
        elif "networkx" in error_msg.lower() or "graph" in error_msg.lower():
            reason = "graph_calculation_failure"
            
        log_subject_exclusion(subject_id, reason, {"error": error_msg})
        return None, None

    # --- Functional Processing ---
    dyn_metrics = None
    try:
        # Similar assumption for functional data
        dyn_metrics = run_functional_pipeline(subject_id, functional_data)
        
        if dyn_metrics is None:
            # If pipeline returns None, it might indicate internal failure or empty data
            raise ValueError("Functional pipeline returned None")
            
    except Exception as e:
        error_msg = str(e)
        reason = "functional_error"
        if "convergence" in error_msg.lower() or "kmeans" in error_msg.lower():
            reason = "convergence_failure"
        elif "empty" in error_msg.lower():
            reason = "empty_data"
            
        log_subject_exclusion(subject_id, reason, {"error": error_msg})
        return None, None

    return struct_metrics, dyn_metrics

def aggregate_metrics_to_csv(structural_list: List[Dict], dynamic_list: List[Dict]) -> None:
    """
    Aggregate lists of metric dictionaries into CSV files.
    """
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed'])
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    if structural_list:
        df_struct = pd.DataFrame(structural_list)
        df_struct.to_csv(processed_dir / 'structural_metrics.csv', index=False)
        print(f"Saved structural metrics to {processed_dir / 'structural_metrics.csv'}")
    else:
        print("No structural metrics to save.")
        
    if dynamic_list:
        df_dyn = pd.DataFrame(dynamic_list)
        df_dyn.to_csv(processed_dir / 'dynamic_metrics.csv', index=False)
        print(f"Saved dynamic metrics to {processed_dir / 'dynamic_metrics.csv'}")
    else:
        print("No dynamic metrics to save.")

def main():
    """
    Main entry point for the pipeline.
    Iterates over available subjects, processes them, and handles exclusions.
    """
    config = get_config_dict()
    ensure_directories()
    
    # In a real scenario, this would iterate over a dataset manifest or directory
    # For this implementation, we assume a list of subject IDs is available or derived from config
    # Placeholder for subject list logic
    subject_ids = config.get('data', {}).get('subject_ids', [])
    
    if not subject_ids:
        print("No subject IDs found in configuration. Exiting.")
        return

    print(f"Starting pipeline for {len(subject_ids)} subjects...")
    
    structural_results = []
    dynamic_results = []
    
    for sid in subject_ids:
        print(f"Processing subject: {sid}")
        try:
            s_metrics, d_metrics = process_subject(sid)
            if s_metrics:
                structural_results.append(s_metrics)
            if d_metrics:
                dynamic_results.append(d_metrics)
        except Exception as e:
            # Catch-all for unexpected errors not handled in process_subject
            log_subject_exclusion(sid, "unexpected_pipeline_error", {"error": str(e)})
            continue
    
    # Save aggregated results
    aggregate_metrics_to_csv(structural_results, dynamic_results)
    
    # Final log summary
    log_data = load_exclusion_log()
    print(f"Pipeline complete. Excluded {log_data['summary'].get('total_excluded', 0)} subjects.")
    print("Exclusion log saved to:", get_exclusion_log_path())

if __name__ == "__main__":
    main()