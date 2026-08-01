import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from src.config import get_project_root, ensure_directories

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def count_available_tumor_types(data_dir: Path) -> int:
    """
    Counts the total number of unique tumor types available for LOO validation.
    
    This function scans the processed data directory for files matching the pattern
    '{tumor_type}_discovery_set.csv' or '{tumor_type}_training_set.csv'.
    It extracts the tumor type prefix and counts unique types.
    
    Args:
        data_dir (Path): Path to the data/processed directory.
        
    Returns:
        int: The count of unique tumor types found.
    """
    if not data_dir.exists():
        logger.warning(f"Processed data directory does not exist: {data_dir}")
        return 0
    
    tumor_types = set()
    
    # Look for processed data files
    # Expected pattern: {tumor_type}_discovery_set.csv or {tumor_type}_training_set.csv
    # We also check raw data if processed doesn't exist yet, but primarily processed
    for file_path in data_dir.iterdir():
        if file_path.is_file() and file_path.suffix == '.csv':
            filename = file_path.stem
            # Split by last underscore to get tumor type
            # e.g., "BRCA_discovery_set" -> "BRCA"
            parts = filename.rsplit('_', 1)
            if len(parts) >= 1:
                tumor_type = parts[0]
                # Basic validation: tumor type should be alphanumeric and reasonable length
                if tumor_type and len(tumor_type) >= 2 and tumor_type.isalnum():
                    tumor_types.add(tumor_type)
    
    logger.info(f"Found {len(tumor_types)} unique tumor types: {sorted(tumor_types)}")
    return len(tumor_types)

def write_feasibility_gate_result(
    gate_path: Path,
    status: str,
    reason: str,
    tumor_type_count: int,
    tumor_types: List[str]
) -> None:
    """
    Writes the feasibility gate result to a JSON file.
    
    Args:
        gate_path (Path): Path to the output JSON file.
        status (str): 'halted' or 'ready'.
        reason (str): Explanation of the status.
        tumor_type_count (int): Number of tumor types found.
        tumor_types (List[str]): List of tumor type identifiers.
    """
    result = {
        "status": status,
        "reason": reason,
        "tumor_type_count": tumor_type_count,
        "tumor_types": tumor_types,
        "gate_name": "loo_feasibility"
    }
    
    # Ensure parent directory exists
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(gate_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Feasibility gate result written to {gate_path}: {status}")

def main() -> int:
    """
    Main entry point for the Pre-Check LOO Feasibility task (T009).
    
    This task:
    1. Counts the total number of tumor types (N) available.
    2. If N < 3, halts execution (exit code 1) and writes a 'halted' gate.
    3. If N >= 3, proceeds and writes a 'ready' gate.
    
    Returns:
        int: Exit code (0 for success/proceed, 1 for halt).
    """
    project_root = get_project_root()
    data_dir = project_root / "data" / "processed"
    gate_path = project_root / "data" / "feasibility_gate_loo.json"
    
    # Ensure directories exist
    ensure_directories()
    
    logger.info("Starting Pre-Check LOO Feasibility (T009)...")
    
    # Count available tumor types
    n = count_available_tumor_types(data_dir)
    
    # Determine status based on count
    if n < 3:
        status = "halted"
        reason = "insufficient_loo_types"
        logger.error(f"LOO Feasibility Check FAILED: Only {n} tumor types found. Minimum required: 3.")
        
        # Write halted gate
        write_feasibility_gate_result(
            gate_path=gate_path,
            status=status,
            reason=reason,
            tumor_type_count=n,
            tumor_types=[]
        )
        
        # Terminate execution with exit code 1
        sys.exit(1)
    else:
        status = "ready"
        reason = "sufficient_loo_types"
        logger.info(f"LOO Feasibility Check PASSED: {n} tumor types found. Proceeding.")
        
        # Write ready gate
        # Note: We list the actual types found for transparency
        tumor_types = sorted(list(set())) # Placeholder, we need to re-collect or pass it
        # Re-collect types for the 'ready' case
        from pathlib import Path
        tumor_types = set()
        if data_dir.exists():
            for file_path in data_dir.iterdir():
                if file_path.is_file() and file_path.suffix == '.csv':
                    filename = file_path.stem
                    parts = filename.rsplit('_', 1)
                    if len(parts) >= 1:
                        tumor_type = parts[0]
                        if tumor_type and len(tumor_type) >= 2 and tumor_type.isalnum():
                            tumor_types.add(tumor_type)
        
        write_feasibility_gate_result(
            gate_path=gate_path,
            status=status,
            reason=reason,
            tumor_type_count=n,
            tumor_types=sorted(list(tumor_types))
        )
        
        return 0

if __name__ == "__main__":
    sys.exit(main())
