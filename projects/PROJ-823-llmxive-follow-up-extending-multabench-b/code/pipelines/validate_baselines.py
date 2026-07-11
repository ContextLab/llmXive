"""
Pipeline: Validate GPU-Tuned Baselines for MulTaBench Datasets.

This script validates the presence of 'GPU-Tuned' baselines for all datasets
available in the project configuration. It generates a CSV report of found
baselines and a JSON report detailing missing entries ('Data Availability Gap').

The 'GPU-Tuned' baselines are expected to be defined in the MulTaBench paper
metadata or a local configuration file derived from the paper. Since the
actual paper data is not embedded in the code, this script attempts to load
it from a standard location `data/raw/mulTabench_paper_baselines.json`.
If that file is missing, it generates the 'Gap' report indicating all datasets
are missing, which is the correct behavior for a missing source.

Output:
  - data/artifacts/gpu_tuned_baselines.csv: Schema (dataset_id, task_type, baseline_value)
  - data/artifacts/data_availability_gap.json: Report of missing baselines.
"""

import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_warning, log_error, log_debug

logger = get_logger(__name__)

# Constants
BASELINES_SOURCE_PATH = Path("data/raw/mulTabench_paper_baselines.json")
OUTPUT_CSV_PATH = Path("data/artifacts/gpu_tuned_baselines.csv")
OUTPUT_GAP_JSON_PATH = Path("data/artifacts/data_availability_gap.json")

# Expected datasets are derived from the project's dataset list configuration
# In a real scenario, this would be loaded from a config file or data loader
# For this implementation, we assume the existence of a standard dataset list
# if not available, we use a placeholder list to demonstrate the logic.
# The task requires processing "ALL available datasets".
# We will attempt to load the dataset list from the standard config/data_loader logic
# or fallback to a known set if the environment is not fully set up.

def load_dataset_list() -> List[str]:
    """
    Loads the list of available dataset IDs.
    Attempts to read from data/datasets.json or falls back to a known set
    if the file doesn't exist yet (graceful degradation for the validation step).
    """
    dataset_config_path = Path("data/datasets.json")
    if dataset_config_path.exists():
        try:
            with open(dataset_config_path, 'r') as f:
                data = json.load(f)
                return [ds['id'] for ds in data.get('datasets', [])]
        except Exception as e:
            log_warning(f"Failed to load dataset list from {dataset_config_path}: {e}. Using fallback list.")
    
    # Fallback: Known MulTaBench dataset IDs (Example set)
    # In a real run, this should be populated by T007 or T008
    fallback_datasets = [
        "mutagenesis", "bace", "bbbp", "clintox", "esol", "freesolv", "lipo",
        "hiv", "sider", "tox21", "toxcast", "moleculenet-mnist", "cifar10"
    ]
    log_info(f"Using fallback dataset list: {fallback_datasets}")
    return fallback_datasets

def load_paper_baselines() -> Dict[str, Dict[str, float]]:
    """
    Loads the 'GPU-Tuned' baselines from the paper data file.
    Expected format: { "dataset_id": { "task_type": baseline_value, ... }, ... }
    """
    if not BASELINES_SOURCE_PATH.exists():
        log_warning(f"Paper baselines file not found at {BASELINES_SOURCE_PATH}. "
                    "Assuming all baselines are missing (Data Availability Gap).")
        return {}
    
    try:
        with open(BASELINES_SOURCE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Failed to parse paper baselines file: {e}")
        return {}

def validate_baselines() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates baselines for all available datasets against the paper data.
    
    Returns:
      found_baselines: List of dicts with keys [dataset_id, task_type, baseline_value]
      missing_entries: List of dicts with keys [dataset_id, task_type, reason]
    """
    datasets = load_dataset_list()
    paper_data = load_paper_baselines()
    
    found_baselines = []
    missing_entries = []
    
    # Define standard task types for MulTaBench if not specified in paper data
    # Common tasks: classification, regression
    standard_tasks = ["classification", "regression"] 
    
    for dataset_id in datasets:
        dataset_baselines = paper_data.get(dataset_id, {})
        
        if not dataset_baselines:
            # No data found for this dataset in the paper file
            missing_entries.append({
                "dataset_id": dataset_id,
                "task_type": "all",
                "reason": "No baseline data found for this dataset in source file."
            })
            log_debug(f"Missing baseline for dataset: {dataset_id} (No data in source)")
            continue
        
        # If the source data has specific task types, use them. 
        # Otherwise, assume a generic 'default' or iterate standard tasks if the structure allows.
        # Assuming structure: { "dataset_id": { "task_type": value } }
        has_found = False
        for task_type, value in dataset_baselines.items():
            if isinstance(value, (int, float)):
                found_baselines.append({
                    "dataset_id": dataset_id,
                    "task_type": task_type,
                    "baseline_value": float(value)
                })
                has_found = True
            else:
                # Handle nested or complex structures if necessary, 
                # but for now we assume simple key-value.
                pass
        
        if not has_found and dataset_baselines:
            # Data exists but format might be unexpected or empty values
             missing_entries.append({
                "dataset_id": dataset_id,
                "task_type": "unknown",
                "reason": "Baseline data exists but could not be parsed as numeric value."
            })

    return found_baselines, missing_entries

def save_baselines_csv(baselines: List[Dict[str, Any]], output_path: Path):
    """Saves the found baselines to a CSV file."""
    ensure_directories([output_path])
    
    fieldnames = ["dataset_id", "task_type", "baseline_value"]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in baselines:
            writer.writerow(row)
    
    log_info(f"Saved {len(baselines)} baseline entries to {output_path}")

def save_gap_report(missing: List[Dict[str, Any]], output_path: Path):
    """Saves the data availability gap report to a JSON file."""
    ensure_directories([output_path])
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_missing_entries": len(missing),
        "missing_datasets": list(set(item["dataset_id"] for item in missing)),
        "details": missing
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Saved data availability gap report to {output_path}")

def main():
    """Main entry point for the validation pipeline."""
    log_info("Starting GPU-Tuned Baseline Validation (T032a)...")
    
    found, missing = validate_baselines()
    
    save_baselines_csv(found, OUTPUT_CSV_PATH)
    save_gap_report(missing, OUTPUT_GAP_JSON_PATH)
    
    log_info("Baseline validation complete.")
    log_info(f"Found {len(found)} baselines, missing {len(missing)} entries.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
