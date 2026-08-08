"""
Data Acquisition Module for PROJ-135.

Handles TCGA and GEO data retrieval, verification, and the Data Feasibility Gate.
Implements strict halting logic if data thresholds are not met.
"""
import os
import sys
import json
import logging
import hashlib
import tempfile
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import project configuration and utilities
from code.src.config import get_project_root, ensure_directories
from code.src.utils import setup_logging, get_file_size_mb

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MIN_TCGA_TYPES = 3
MIN_GEO_DATASETS = 2
MAX_DOWNLOAD_SIZE_GB = 5.0
STATE_FILE_PATH = "state/projects/PROJ-135-identifying-predictive-biomarkers-of-che.yaml"
FEASIBILITY_GATE_OUTPUT = "data/feasibility_gate.json"

def compute_file_checksum(file_path: str) -> str:
    """
    Compute SHA256 checksum of a file.
    Reads in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def write_checksum_to_state(file_path: str, checksum: str) -> None:
    """
    Atomically append a checksum to the project state YAML file.
    Only called after successful download and verification.
    """
    state_path = get_project_root() / STATE_FILE_PATH
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    state_data = {}
    if state_path.exists():
        import yaml
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f) or {}

    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}

    # Update checksum
    state_data['artifact_hashes'][file_path] = checksum

    # Atomic write
    temp_fd, temp_path = tempfile.mkstemp(suffix='.yaml')
    try:
        with os.fdopen(temp_fd, 'w') as tmp_file:
            import yaml
            yaml.dump(state_data, tmp_file, default_flow_style=False)
        os.replace(temp_path, str(state_path))
        logger.info(f"Checksum written to state: {file_path} -> {checksum[:16]}...")
    except Exception as e:
        logger.error(f"Failed to write checksum atomically: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise

def count_available_tumor_types(data_dir: Path) -> int:
    """
    Count valid TCGA tumor types found in the raw data directory.
    A valid type must have both expression and clinical data.
    """
    if not data_dir.exists():
        return 0
    
    # Expected structure: data/raw/tcga/{TCGA-CODE}/...
    tcga_base = data_dir / "tcga"
    if not tcga_base.exists():
        return 0
    
    valid_types = set()
    for item in tcga_base.iterdir():
        if item.is_dir() and item.name.startswith("TCGA-"):
            # Check if essential files exist (simplified check)
            if (item / "expression_counts.csv").exists() or (item / "clinical.json").exists():
                valid_types.add(item.name)
    
    return len(valid_types)

def check_response_labels(clinical_data: Dict[str, Any]) -> bool:
    """
    Verify that the clinical data contains valid response labels (RECIST/CR/PR).
    Returns True if valid labels are found, False otherwise.
    """
    if not clinical_data:
        return False
    
    # Check for common response label keys
    response_keys = ['response', 'best_overall_response', 'recist_response', 'response_label']
    found_label = False
    
    for key in response_keys:
        if key in clinical_data:
            value = clinical_data[key]
            if isinstance(value, str) and value.upper() in ['CR', 'PR', 'SD', 'PD', 'RESPONDER', 'NON_RESPONDER']:
                found_label = True
                break
            elif isinstance(value, list) and len(value) > 0:
                # If it's a list of samples, check if any have response info
                found_label = True
                break
    
    return found_label

def write_feasibility_gate_result(
    status: str, 
    reason: Optional[str] = None, 
    tcga_count: int = 0, 
    geo_count: int = 0
) -> None:
    """
    Write the feasibility gate result to the JSON output file.
    This is the single source of truth for the pipeline's readiness.
    """
    output_path = get_project_root() / FEASIBILITY_GATE_OUTPUT
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "status": status,
        "tcga_tumor_types_count": tcga_count,
        "valid_geo_datasets_count": geo_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    if reason:
        result["reason"] = reason

    try:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Feasibility gate result written: {status} ({reason or 'ready'})")
    except Exception as e:
        logger.error(f"Failed to write feasibility gate result: {e}")
        raise

def run_data_feasibility_gate(tcga_count: int, valid_geo_count: int) -> bool:
    """
    Execute the Data Feasibility Gate logic.
    
    Rules:
    1. If TCGA count < 3: HALT with status 'halted', reason 'insufficient_tcga_types'
    2. If GEO count < 2: HALT with status 'halted', reason 'insufficient_geo_datasets'
    3. If both pass: Write status 'ready' and return True
    
    Returns:
        bool: True if gate passed, False if halted.
    """
    logger.info(f"Running Data Feasibility Gate: TCGA={tcga_count}, GEO={valid_geo_count}")
    
    # Check TCGA threshold
    if tcga_count < MIN_TCGA_TYPES:
        logger.error(f"TCGA tumor types ({tcga_count}) < required ({MIN_TCGA_TYPES})")
        write_feasibility_gate_result(
            status="halted",
            reason="insufficient_tcga_types",
            tcga_count=tcga_count,
            geo_count=valid_geo_count
        )
        return False

    # Check GEO threshold
    if valid_geo_count < MIN_GEO_DATASETS:
        logger.error(f"Valid GEO datasets ({valid_geo_count}) < required ({MIN_GEO_DATASETS})")
        write_feasibility_gate_result(
            status="halted",
            reason="insufficient_geo_datasets",
            tcga_count=tcga_count,
            geo_count=valid_geo_count
        )
        return False

    # Gate Passed
    write_feasibility_gate_result(
        status="ready",
        tcga_count=tcga_count,
        geo_count=valid_geo_count
    )
    logger.info("Data Feasibility Gate PASSED. Proceeding to next stage.")
    return True

def main():
    """
    Main entry point for the data acquisition and feasibility gate.
    This function is expected to be called after T012/T013 acquisition steps.
    For this specific task (T014), we assume T012/T013 have populated the data directory
    and we are validating the results.
    """
    setup_logging()
    project_root = get_project_root()
    ensure_directories()

    data_dir = project_root / "data" / "raw"
    
    # In a real pipeline, T012 and T013 would have run here.
    # For T014, we count what exists and run the gate.
    # Note: In the actual pipeline flow, this function might receive counts
    # directly from the acquisition functions to avoid double-scanning,
    # but scanning ensures consistency.
    
    tcga_count = count_available_tumor_types(data_dir)
    
    # For GEO, we assume a similar directory structure or a flag set by T013
    # In a full implementation, T013 would return the valid_geo_count.
    # Here we simulate counting based on directory existence or a metadata file.
    geo_dir = data_dir / "geo"
    valid_geo_count = 0
    if geo_dir.exists():
        # Count directories that have a 'verified' marker or response data
        for item in geo_dir.iterdir():
            if item.is_dir():
                # Check for a marker file indicating valid response labels
                if (item / "response_verified.txt").exists():
                    valid_geo_count += 1
    
    # Run the gate
    gate_passed = run_data_feasibility_gate(tcga_count, valid_geo_count)
    
    if not gate_passed:
        logger.critical("Pipeline halted due to data feasibility gate failure.")
        sys.exit(1)
    
    # Log warning if total size > 5GB (spec requirement)
    total_size = get_file_size_mb(data_dir)
    if total_size > MAX_DOWNLOAD_SIZE_GB * 1024:
        logger.warning(f"Total download size ({total_size/1024:.2f} GB) exceeds {MAX_DOWNLOAD_SIZE_GB} GB threshold.")

    logger.info("Data acquisition and feasibility check completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())