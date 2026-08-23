import os
import sys
import json
import traceback
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any

from config import get_config_dict, ensure_directories
from preprocess.structural import process_subject_structural_metrics
from preprocess.functional import run_functional_pipeline
from utils.cpu_optimization import set_random_seed

# Configuration
CONFIG = get_config_dict()
RANDOM_SEED = CONFIG.get("random_seed", 42)
SPARSITY_THRESHOLD = CONFIG.get("sparsity_threshold", 0.90)
LOG_PATH = Path("data/logs/exclusion_log.json")

def get_exclusion_log_path() -> Path:
    """Return the path to the exclusion log file."""
    ensure_directories()
    return LOG_PATH

def load_exclusion_log() -> Dict[str, Any]:
    """Load the exclusion log from disk, or return an empty structure if missing."""
    path = get_exclusion_log_path()
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"excluded_subjects": [], "total_processed": 0, "total_excluded": 0}
    return {"excluded_subjects": [], "total_processed": 0, "total_excluded": 0}

def save_exclusion_log(log_data: Dict[str, Any]) -> None:
    """Save the exclusion log to disk."""
    ensure_directories()
    path = get_exclusion_log_path()
    with open(path, 'w') as f:
        json.dump(log_data, f, indent=2)

def log_subject_exclusion(subject_id: str, reason: str, details: Optional[Dict] = None) -> None:
    """
    Log a subject exclusion to the exclusion log.
    
    Args:
        subject_id: The ID of the excluded subject.
        reason: The reason for exclusion (e.g., 'sparsity', 'convergence_failure').
        details: Optional dictionary of additional details.
    """
    log_data = load_exclusion_log()
    entry = {
        "subject_id": subject_id,
        "reason": reason,
        "details": details or {},
        "timestamp": pd.Timestamp.now().isoformat()
    }
    log_data["excluded_subjects"].append(entry)
    log_data["total_excluded"] = len(log_data["excluded_subjects"])
    save_exclusion_log(log_data)
    print(f"[EXCLUSION] Subject {subject_id} excluded: {reason}")

def process_subject(subject_id: str, data_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Process a single subject's structural and functional data.
    
    Returns:
        A dictionary containing structural and dynamic metrics if successful.
        Returns None if the subject is excluded.
    """
    set_random_seed(RANDOM_SEED)
    
    try:
        # 1. Structural Processing
        struct_metrics = process_subject_structural_metrics(subject_id, data_dir)
        
        if struct_metrics is None:
            # process_subject_structural_metrics handles internal sparsity checks
            # and raises exceptions or returns None if excluded.
            # We need to catch the specific reason if possible, otherwise generic.
            log_subject_exclusion(subject_id, "structural_processing_failed")
            return None

        # 2. Functional Processing
        dynamic_metrics = run_functional_pipeline(subject_id, data_dir)
        
        if dynamic_metrics is None:
            log_subject_exclusion(subject_id, "functional_processing_failed")
            return None

        return {
            "subject_id": subject_id,
            "structural": struct_metrics,
            "dynamic": dynamic_metrics
        }

    except Exception as e:
        error_msg = str(e)
        reason = "unknown_error"
        
        # Categorize error for logging
        if "sparsity" in error_msg.lower() or "sparsity" in str(type(e)).lower():
            reason = "sparsity"
        elif "convergence" in error_msg.lower() or "kmeans" in error_msg.lower():
            reason = "convergence_failure"
        
        log_subject_exclusion(subject_id, reason, {"error_message": error_msg})
        traceback.print_exc()
        return None

def aggregate_metrics_to_csv(results: List[Dict[str, Any]]) -> None:
    """
    Aggregate processed metrics into CSV files.
    
    Args:
        results: List of dictionaries containing subject metrics.
    """
    if not results:
        print("No results to aggregate.")
        return

    struct_rows = []
    dynamic_rows = []

    for res in results:
        sid = res["subject_id"]
        
        # Flatten structural metrics
        s_data = res["structural"]
        struct_rows.append({
            "subject_id": sid,
            "global_efficiency": s_data.get("global_efficiency"),
            "avg_clustering": s_data.get("avg_clustering"),
            "modularity": s_data.get("modularity"),
            "density": s_data.get("density")
        })

        # Flatten dynamic metrics
        d_data = res["dynamic"]
        dynamic_rows.append({
            "subject_id": sid,
            "num_visited_states": d_data.get("num_visited_states"),
            "mean_dwell_time": d_data.get("mean_dwell_time"),
            "state_probs": json.dumps(d_data.get("state_probs", {}))
        })

    # Ensure directories exist
    ensure_directories()

    # Write Structural CSV
    df_struct = pd.DataFrame(struct_rows)
    struct_path = Path("data/processed/structural_metrics.csv")
    df_struct.to_csv(struct_path, index=False)
    print(f"Saved structural metrics to {struct_path}")

    # Write Dynamic CSV
    df_dynamic = pd.DataFrame(dynamic_rows)
    dynamic_path = Path("data/processed/dynamic_metrics.csv")
    df_dynamic.to_csv(dynamic_path, index=False)
    print(f"Saved dynamic metrics to {dynamic_path}")

def main():
    """Main entry point for the pipeline."""
    print("Starting llmXive Pipeline - T020 Integration")
    
    # Initialize log
    ensure_directories()
    log_data = load_exclusion_log()
    log_data["total_processed"] = 0
    save_exclusion_log(log_data)

    # Mock data directory for demonstration if real data not present
    # In a real run, this would point to the actual HCP data directory
    data_root = Path("data/raw")
    if not data_root.exists():
        print("Warning: data/raw directory not found. Skipping batch processing.")
        # Initialize an empty log with 0 processed
        log_data = load_exclusion_log()
        log_data["total_processed"] = 0
        save_exclusion_log(log_data)
        return

    # In a real scenario, we would iterate over subject IDs found in data_root
    # For this implementation, we assume a list of subjects is provided or discovered
    # Since T006/T007 setup implies data exists, we attempt to list subjects.
    # If empty, we log that no subjects were found.
    subject_ids = [f"sub-{i:03d}" for i in range(1, 4)] # Placeholder for discovery logic
    
    # If using a real loader, we would do:
    # subjects = loader.discover_subjects(data_root)
    
    processed_results = []
    
    for sid in subject_ids:
        # Check if subject data exists (mock check)
        subj_dir = data_root / sid
        if not subj_dir.exists():
            # Log exclusion for missing data
            log_subject_exclusion(sid, "data_missing", {"path": str(subj_dir)})
            continue
        
        result = process_subject(sid, subj_dir)
        if result:
            processed_results.append(result)
    
    # Update total processed count
    log_data = load_exclusion_log()
    log_data["total_processed"] = len(processed_results)
    save_exclusion_log(log_data)

    # Aggregate results
    aggregate_metrics_to_csv(processed_results)
    
    print(f"Pipeline complete. Processed: {len(processed_results)}, Excluded: {log_data['total_excluded']}")
    print(f"Exclusion log saved to: {get_exclusion_log_path()}")

if __name__ == "__main__":
    main()
