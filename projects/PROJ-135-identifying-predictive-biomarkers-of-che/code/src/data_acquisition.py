import os
import sys
import json
import logging
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.config import get_project_root, ensure_directories
from src.utils import setup_logging

logger = setup_logging()

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def write_checksum_to_state(checksums: Dict[str, str], state_file: Path) -> None:
    """Write checksums to the project state file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if state_file.exists():
        with open(state_file, 'r') as f:
            try:
                state_data = json.load(f)
            except json.JSONDecodeError:
                state_data = {}
    else:
        state_data = {}

    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}

    state_data['artifact_hashes'].update(checksums)

    with open(state_file, 'w') as f:
        json.dump(state_data, f, indent=2)

    logger.info(f"Checksums written to {state_file}")

def write_feasibility_gate_result(
    gate_status: str,
    available_tcga_types: List[str],
    available_geo_datasets: List[str],
    output_file: Path
) -> None:
    """
    Write the feasibility gate result to results/validation_status.json.
    gate_status: 'pass' or 'fail'
    """
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "feasibility_gate": gate_status,
        "available_types": available_tcga_types,
        "available_geo_datasets": available_geo_datasets,
        "tcga_count": len(available_tcga_types),
        "geo_count": len(available_geo_datasets),
        "message": ""
    }

    if gate_status == "pass":
        result["message"] = "Feasibility Gate Passed: Sufficient TCGA and GEO data available."
        logger.info(f"Feasibility Gate PASSED. TCGA types: {len(available_tcga_types)}, GEO datasets: {len(available_geo_datasets)}")
    else:
        result["message"] = "Feasibility Gate FAILED: Insufficient data available."
        logger.error(f"Feasibility Gate FAILED. TCGA types: {len(available_tcga_types)}, GEO datasets: {len(available_geo_datasets)}")

    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

def fetch_geo_dataset(accession: str, output_dir: Path) -> bool:
    """
    Fetch a GEO dataset. Returns True if successful and has valid response labels.
    In a real implementation, this would use GEOquery (via R) or a Python wrapper.
    For this task, we simulate the check based on the existence of a marker file 
    created by T013a, as per the task dependency flow.
    """
    # In the actual pipeline, T013a creates raw data. We check for that.
    # Expected pattern: data/raw/GEO_{accession}/processed/ or similar
    # Since T013a is "Implement R Script", we assume it writes a status file or data.
    # We will check for a marker file created by T013a: data/raw/{accession}_status.json
    
    status_file = output_dir.parent / f"{accession}_status.json"
    if not status_file.exists():
        logger.warning(f"GEO dataset {accession} status file not found. Skipping.")
        return False

    try:
        with open(status_file, 'r') as f:
            status_data = json.load(f)
        # Check if it has response labels
        if status_data.get('has_response_labels', False):
            logger.info(f"GEO dataset {accession} found with response labels.")
            return True
        else:
            logger.warning(f"GEO dataset {accession} found but lacks response labels.")
            return False
    except Exception as e:
        logger.error(f"Error reading status for {accession}: {e}")
        return False

def parse_geo_samples(accession: str, data_dir: Path) -> int:
    """
    Parse GEO samples and count valid ones.
    Returns count.
    """
    # Placeholder for actual parsing logic
    # In real flow, this reads the downloaded data
    return 0

def get_valid_geo_count(geo_ids: List[str], data_dir: Path) -> List[str]:
    """
    Iterate through configured GEO IDs and return list of valid ones.
    """
    valid_datasets = []
    for accession in geo_ids:
        if fetch_geo_dataset(accession, data_dir / accession):
            valid_datasets.append(accession)
    return valid_datasets

def main():
    """
    Main entry point for Data Feasibility Gate (T014).
    Logic:
    1. Read results/validation_status.json from T012a (TCGA) and T013a (GEO).
    2. Check if >=3 TCGA types and >=2 GEO datasets with response labels are available.
    3. Write results/validation_status.json with feasibility_gate status.
    4. If fail, log critical error and exit with code 1.
    """
    project_root = get_project_root()
    results_dir = project_root / "results"
    data_raw_dir = project_root / "data" / "raw"
    
    ensure_directories()

    # Paths
    validation_status_file = results_dir / "validation_status.json"
    
    # Load TCGA status (from T012a)
    # T012a writes to results/validation_status.json with 'available_types'
    # We need to distinguish TCGA vs GEO. Let's assume T012a wrote a specific file 
    # or we read the existing one and check source.
    # Per T012a description: "Write ... results/validation_status.json with the list of available types."
    # Per T013a description: "Write raw data to data/raw/."
    # To avoid overwriting T012a's file before T014 runs, T014 should read it.
    
    if not validation_status_file.exists():
        logger.critical("results/validation_status.json not found. T012a (TCGA Download) may not have run.")
        sys.exit(1)

    try:
        with open(validation_status_file, 'r') as f:
            tCGA_status = json.load(f)
    except Exception as e:
        logger.critical(f"Error reading results/validation_status.json: {e}")
        sys.exit(1)

    # Extract TCGA types
    # T012a output structure assumption: {'available_types': [...], ...}
    tcga_types = tCGA_status.get('available_types', [])
    if not isinstance(tcga_types, list):
        tcga_types = []
    
    # Check GEO status
    # T013a writes raw data. We need a status file from T013a to know if it succeeded.
    # Let's assume T013a writes data/raw/geo_status.json or similar.
    # Or we iterate the data/raw directory for GEO accession folders.
    # Task T013a says: "Write raw data to data/raw/."
    # We will check for folders named like 'GSE...' in data/raw.
    
    geo_ids = ['GSE25055', 'GSE42752'] # Default from T004
    valid_geo = []
    
    for geo_id in geo_ids:
        # Check if data exists for this GEO ID
        geo_path = data_raw_dir / geo_id
        if geo_path.exists() and geo_path.is_dir():
            # Check for response labels (simulated by checking a marker file or metadata)
            # T013a logic: "Filter for datasets with response annotations."
            # We assume T013a only creates the folder if it has response annotations.
            # Or we check for a specific file like 'response_labels.csv'
            marker = geo_path / "response_labels.csv"
            if marker.exists():
                valid_geo.append(geo_id)
            else:
                logger.warning(f"GEO dataset {geo_id} found but no response labels marker.")
        else:
            logger.warning(f"GEO dataset {geo_id} not found in data/raw.")

    # Validation Logic
    min_tcga = 3
    min_geo = 2

    tcga_count = len(tcga_types)
    geo_count = len(valid_geo)

    gate_passed = True
    reason = ""

    if tcga_count < min_tcga:
        gate_passed = False
        reason += f"TCGA types ({tcga_count}) < {min_tcga}. "
    
    if geo_count < min_geo:
        gate_passed = False
        reason += f"GEO datasets ({geo_count}) < {min_geo}. "

    # Write Result
    write_feasibility_gate_result(
        gate_status="pass" if gate_passed else "fail",
        available_tcga_types=tcga_types,
        available_geo_datasets=valid_geo,
        output_file=validation_status_file
    )

    if not gate_passed:
        logger.critical(f"Data Feasibility Gate FAILED: {reason}")
        sys.exit(1)
    
    logger.info("Data Feasibility Gate PASSED. Proceeding to next stage.")

if __name__ == "__main__":
    main()