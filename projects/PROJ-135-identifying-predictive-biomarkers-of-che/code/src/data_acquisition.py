import os
import sys
import json
import logging
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import shared utilities and config from the project structure
from src.config import get_project_root, ensure_directories
from src.utils import setup_logging, get_file_size_mb, update_state_artifact_hashes

# Configure logging
logger = logging.getLogger(__name__)

# Constants for Feasibility Gates
MIN_TCGA_TYPES = 3
MIN_GEO_DATASETS = 2
MAX_DOWNLOAD_SIZE_GB = 5.0

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        raise

def write_checksum_to_state(checksum: str, artifact_name: str, state_path: Path) -> None:
    """Atomically write checksum to the state file."""
    try:
        if state_path.exists():
            with open(state_path, 'r') as f:
                state_data = json.load(f)
        else:
            state_data = {"artifact_hashes": {}}

        if "artifact_hashes" not in state_data:
            state_data["artifact_hashes"] = {}

        state_data["artifact_hashes"][artifact_name] = checksum

        # Atomic write
        temp_path = state_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(state_data, f, indent=2)
        os.replace(temp_path, state_path)
        logger.info(f"Checksum written to state: {artifact_name}")
    except Exception as e:
        logger.error(f"Failed to write checksum to state: {e}")
        raise

def check_response_labels(metadata: Dict[str, Any]) -> bool:
    """
    Check if the dataset metadata contains valid response labels.
    Returns True if labels are present, False otherwise.
    """
    # Check for common response label keys
    response_keys = ['response', 'response_label', 'recist', 'treatment_response', 'outcome']
    if not metadata or not isinstance(metadata, dict):
        return False

    for key in response_keys:
        if key in metadata and metadata[key] is not None and metadata[key] != '':
            return True
    
    # Check if any column in data contains response info
    if 'columns' in metadata:
        for col in metadata['columns']:
            if any(k in str(col).lower() for k in response_keys):
                return True
    
    return False

def fetch_geo_dataset(geo_id: str, output_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Fetch a GEO dataset by ID.
    Returns metadata if successful, None if failed.
    """
    # Placeholder for actual GEO fetching logic (T013 implementation)
    # In a real implementation, this would use GEOquery or similar
    # For now, we simulate the structure expected by the feasibility gate
    logger.info(f"Attempting to fetch GEO dataset: {geo_id}")
    
    # This is a placeholder - in real implementation, this would:
    # 1. Download the dataset
    # 2. Verify response labels
    # 3. Return metadata
    # For T014, we assume this function is called by T013 and returns valid metadata
    return {
        "geo_id": geo_id,
        "has_response_labels": True,
        "file_path": str(output_dir / f"{geo_id}.txt")
    }

def parse_geo_metadata(dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Parse and validate GEO dataset metadata."""
    if not dataset or "has_response_labels" not in dataset:
        return {"valid": False}
    
    return {
        "valid": dataset["has_response_labels"],
        "geo_id": dataset.get("geo_id"),
        "file_path": dataset.get("file_path")
    }

def run_geo_acquisition(geo_ids: List[str], output_dir: Path) -> Dict[str, Any]:
    """
    Run GEO acquisition for multiple datasets.
    Returns a summary with valid_geo_count.
    """
    valid_geo_count = 0
    failed_geo_ids = []
    
    for geo_id in geo_ids:
        try:
            dataset = fetch_geo_dataset(geo_id, output_dir)
            if dataset:
                metadata = parse_geo_metadata(dataset)
                if metadata["valid"]:
                    valid_geo_count += 1
                    # Write checksum if file exists
                    if dataset.get("file_path") and os.path.exists(dataset["file_path"]):
                        checksum = compute_file_checksum(dataset["file_path"])
                        write_checksum_to_state(checksum, f"geo_{geo_id}", get_project_root() / "state" / "projects" / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml")
                else:
                    logger.warning(f"GEO dataset {geo_id} lacks response labels, skipping")
                    failed_geo_ids.append(geo_id)
            else:
                logger.error(f"Failed to fetch GEO dataset: {geo_id}")
                failed_geo_ids.append(geo_id)
        except Exception as e:
            logger.error(f"Error processing GEO dataset {geo_id}: {e}")
            failed_geo_ids.append(geo_id)
    
    return {
        "valid_geo_count": valid_geo_count,
        "failed_geo_ids": failed_geo_ids,
        "total_attempted": len(geo_ids)
    }

def count_available_tumor_types(data_dir: Path) -> int:
    """
    Count the number of valid TCGA tumor types available.
    Looks for processed data files or metadata indicating available types.
    """
    # In a real implementation, this would scan the data directory for valid TCGA data
    # For T014, we assume T012 has already populated this information
    # We check for the presence of processed data files for different tumor types
    if not data_dir.exists():
        return 0
    
    # Look for processed data files (e.g., *_discovery_set.csv or similar)
    # In a real implementation, this would be more sophisticated
    tumor_types = set()
    for file in data_dir.glob("*.csv"):
        # Extract tumor type from filename (assumes format like BRCA_discovery_set.csv)
        parts = file.stem.split('_')
        if len(parts) >= 2:
            tumor_type = parts[0]
            # Validate tumor type (should be 2-4 letter codes)
            if len(tumor_type) >= 2 and len(tumor_type) <= 4 and tumor_type.isupper():
                tumor_types.add(tumor_type)
    
    return len(tumor_types)

def write_feasibility_gate_result(status: str, reason: str, output_path: Path) -> None:
    """Write the feasibility gate result to JSON."""
    result = {
        "status": status,
        "reason": reason if reason else None,
        "timestamp": None  # Could add timestamp if needed
    }
    
    try:
        temp_path = output_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(result, f, indent=2)
        os.replace(temp_path, output_path)
        logger.info(f"Feasibility gate result written: {status}")
    except Exception as e:
        logger.error(f"Failed to write feasibility gate result: {e}")
        raise

def run_feasibility_gate(tcga_types_count: int, geo_count: int, data_dir: Path) -> bool:
    """
    Run the Data Feasibility Gate checks.
    
    Returns True if all gates pass, False otherwise.
    If any gate fails, writes the result to data/feasibility_gate.json and exits.
    """
    output_path = data_dir / "feasibility_gate.json"
    
    # Ensure data directory exists
    ensure_directories(data_dir)
    
    # Log total download size warning if applicable
    total_size_gb = 0.0
    if data_dir.exists():
        for item in data_dir.rglob("*"):
            if item.is_file():
                total_size_gb += get_file_size_mb(str(item)) / 1024.0
    
    if total_size_gb > MAX_DOWNLOAD_SIZE_GB:
        logger.warning(f"Total download size ({total_size_gb:.2f} GB) exceeds {MAX_DOWNLOAD_SIZE_GB} GB threshold")
    
    # TCGA Gate
    if tcga_types_count < MIN_TCGA_TYPES:
        logger.error(f"TCGA Gate FAILED: Found {tcga_types_count} tumor types, required >= {MIN_TCGA_TYPES}")
        write_feasibility_gate_result("halted", "insufficient_tcga_types", output_path)
        return False
    
    # GEO Gate
    if geo_count < MIN_GEO_DATASETS:
        logger.error(f"GEO Gate FAILED: Found {geo_count} valid GEO datasets, required >= {MIN_GEO_DATASETS}")
        write_feasibility_gate_result("halted", "insufficient_geo_datasets", output_path)
        return False
    
    # All gates passed
    logger.info(f"Feasibility Gate PASSED: TCGA={tcga_types_count}, GEO={geo_count}")
    write_feasibility_gate_result("ready", None, output_path)
    return True

def main():
    """Main entry point for data acquisition and feasibility gate."""
    # Setup logging
    setup_logging()
    
    # Get project root and directories
    project_root = get_project_root()
    data_dir = project_root / "data"
    
    # Ensure directories exist
    ensure_directories(data_dir)
    
    # In a real implementation, this would:
    # 1. Run T012 (TCGA acquisition) to get tcga_types_count
    # 2. Run T013 (GEO acquisition) to get geo_count
    # 3. Call run_feasibility_gate with those counts
    
    # For now, we simulate the counts (in real implementation, these come from T012/T013)
    # This is a placeholder - the actual implementation would call the acquisition functions
    tcga_types_count = count_available_tumor_types(data_dir)
    
    # For GEO count, we would need to run the acquisition first
    # In a real pipeline, this would be passed from T013
    geo_count = 0  # Placeholder - would be updated by T013
    
    # Run feasibility gate
    success = run_feasibility_gate(tcga_types_count, geo_count, data_dir)
    
    if not success:
        logger.error("Feasibility gate failed. Exiting with code 1.")
        sys.exit(1)
    
    logger.info("Feasibility gate passed. Proceeding to next stage.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
