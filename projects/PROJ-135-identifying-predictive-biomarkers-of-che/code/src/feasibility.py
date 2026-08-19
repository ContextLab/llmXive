import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import from local config to get project root and thresholds
# Assuming config.py is in the same package structure as defined in API surface
try:
    from .config import get_project_root
except ImportError:
    # Fallback for direct execution or different import context
    from config import get_project_root

logger = logging.getLogger(__name__)

def count_available_tumor_types() -> int:
    """
    Counts the number of valid TCGA tumor types found in the processed data.
    Reads data/processed/tcga_samples.json to determine availability.
    Returns the count of unique tumor_type values found.
    """
    project_root = get_project_root()
    tcga_samples_path = project_root / "data" / "processed" / "tcga_samples.json"
    
    if not tcga_samples_path.exists():
        logger.warning(f"TCGA samples file not found at {tcga_samples_path}. Counting 0 types.")
        return 0
    
    try:
        with open(tcga_samples_path, 'r') as f:
            samples_data = json.load(f)
        
        # Handle cases where data might be a list of samples or a dict with a 'samples' key
        if isinstance(samples_data, dict) and 'samples' in samples_data:
            samples = samples_data['samples']
        elif isinstance(samples_data, list):
            samples = samples_data
        else:
            logger.error("Unexpected format in tcga_samples.json")
            return 0
        
        unique_types = set()
        for sample in samples:
            if 'tumor_type' in sample:
                unique_types.add(sample['tumor_type'])
        
        count = len(unique_types)
        logger.info(f"Found {count} unique TCGA tumor types: {sorted(unique_types)}")
        return count
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse tcga_samples.json: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error counting tumor types: {e}")
        return 0

def get_valid_geo_count() -> int:
    """
    Counts the number of valid GEO datasets found in the processed data.
    Reads data/processed/geo_samples.json to determine availability.
    Returns the count of unique datasets (or samples if dataset ID is not explicit) 
    that have valid response labels.
    Based on T013 logic, this counts datasets with response labels.
    """
    project_root = get_project_root()
    geo_samples_path = project_root / "data" / "processed" / "geo_samples.json"
    
    if not geo_samples_path.exists():
        logger.warning(f"GEO samples file not found at {geo_samples_path}. Counting 0 datasets.")
        return 0
    
    try:
        with open(geo_samples_path, 'r') as f:
            samples_data = json.load(f)
        
        # We assume the file structure might group by dataset or be a flat list with dataset_id
        # T013 mentions 'valid_geo_count' based on datasets with response labels.
        # If the file is a list of samples, we need to count unique dataset_ids that have valid labels.
        if isinstance(samples_data, dict) and 'samples' in samples_data:
            samples = samples_data['samples']
        elif isinstance(samples_data, list):
            samples = samples_data
        else:
            logger.error("Unexpected format in geo_samples.json")
            return 0
        
        # Track valid datasets. A dataset is valid if it has samples with response labels.
        # We assume each sample has a 'dataset_id' and a 'response_label'.
        valid_datasets = set()
        
        for sample in samples:
            if 'response_label' in sample and sample['response_label'] is not None and sample['response_label'] != '':
                if 'dataset_id' in sample:
                    valid_datasets.add(sample['dataset_id'])
                else:
                    # If no dataset_id, treat each sample as a potential dataset entry or log warning
                    # For safety, if we can't group, we might count unique sample_ids or just assume 1 if any exist
                    # But per T013, we count datasets. Let's assume 'dataset_id' is present for valid geo samples.
                    logger.warning("Sample in geo_samples.json missing 'dataset_id' but has response_label.")
        
        count = len(valid_datasets)
        logger.info(f"Found {count} valid GEO datasets with response labels.")
        return count
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse geo_samples.json: {e}")
        return 0
    except Exception as e:
        logger.error(f"Error counting valid GEO datasets: {e}")
        return 0

def write_feasibility_gate_result(
    status: str, 
    reason: str = "", 
    tcga_count: int = 0, 
    geo_count: int = 0
) -> None:
    """
    Writes the feasibility gate result to data/feasibility_gate.json.
    
    Args:
        status: One of "ready", "halted", "pending_tcga_check", "pending_geo_check".
        reason: Explanation for the status (e.g., "insufficient_tcga_types").
        tcga_count: Number of TCGA types found.
        geo_count: Number of valid GEO datasets found.
    """
    project_root = get_project_root()
    gate_path = project_root / "data" / "feasibility_gate.json"
    
    result = {
        "status": status,
        "reason": reason,
        "tcga_count": tcga_count,
        "geo_count": geo_count
    }
    
    # Ensure data directory exists
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(gate_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Feasibility gate result written to {gate_path}: {result}")

def main() -> int:
    """
    Main entry point for the Data Feasibility Gate (T014).
    
    Logic:
    1. Check TEST_MODE environment variable.
    2. Count TCGA tumor types and GEO valid datasets.
    3. Evaluate against thresholds (TCGA >= 3, GEO >= 2).
    4. Write results to data/feasibility_gate.json.
    5. Exit with code 1 if halted, 0 if ready.
    
    Returns:
        int: Exit code (0 for success/ready, 1 for failure/halted).
    """
    test_mode = os.getenv("TEST_MODE", "False").lower() == "true"
    logger.info(f"Running Feasibility Gate. TEST_MODE={test_mode}")
    
    tcga_count = count_available_tumor_types()
    geo_count = get_valid_geo_count()
    
    # Log warning if total download size > 5GB (Spec FR-001)
    # This is a heuristic check; in a real scenario, we might sum file sizes.
    # For now, we log if counts are high as a proxy for size, or check a manifest if available.
    # Since we don't have a manifest here, we'll log a generic warning if counts are substantial.
    if tcga_count + geo_count > 0:
        logger.warning("Warning: Total download size may exceed 5 GB (Spec FR-001). Please verify disk space.")
    
    status = "ready"
    reason = ""
    exit_code = 0
    
    if not test_mode:
        # TCGA Gate
        if tcga_count < 3:
            status = "halted"
            reason = "insufficient_tcga_types"
            exit_code = 1
            logger.error(f"TCGA Gate Failed: Found {tcga_count} types, required >= 3.")
        
        # GEO Gate (only if TCGA didn't already halt, or we check both)
        # The spec says "If TCGA < 3 OR GEO < 2 ... Terminate". 
        # We should check both and report the first failure or a combined one.
        # The task description implies checking both and halting if either fails.
        if geo_count < 2 and status != "halted":
            status = "halted"
            reason = "insufficient_geo_datasets"
            exit_code = 1
            logger.error(f"GEO Gate Failed: Found {geo_count} valid datasets, required >= 2.")
        
        # If both fail, we can report the first one encountered or a combined reason.
        # Let's prioritize TCGA failure if both are insufficient.
        if tcga_count < 3 and geo_count < 2:
            status = "halted"
            reason = "insufficient_tcga_types_and_geo_datasets"
            exit_code = 1
            logger.error("Both TCGA and GEO gates failed.")
    else:
        logger.info("TEST_MODE is True. Skipping strict feasibility checks.")
        if tcga_count < 3:
            logger.warning(f"TEST_MODE: TCGA count ({tcga_count}) is below threshold (3).")
        if geo_count < 2:
            logger.warning(f"TEST_MODE: GEO count ({geo_count}) is below threshold (2).")
    
    write_feasibility_gate_result(status, reason, tcga_count, geo_count)
    
    if exit_code != 0:
        logger.critical(f"Feasibility Gate Halted. Reason: {reason}. Exiting with code {exit_code}.")
    
    return exit_code

if __name__ == "__main__":
    # Configure logging if run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    sys.exit(main())
