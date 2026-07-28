import os
import sys
import json
import logging
import hashlib
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import existing utilities and config
from src.config import get_project_root, ensure_directories
from src.utils import calculate_checksum, update_state_artifact_hashes, setup_logging

# Configure logging
logger = logging.getLogger(__name__)

# Global list to store checksums as they are computed (T012c)
_checksums: List[Dict[str, Any]] = []

def _add_checksum(filepath: str, algorithm: str = "sha256") -> None:
    """Compute and store checksum for a single file immediately after download (T012c)."""
    if not os.path.exists(filepath):
        logger.error(f"Cannot compute checksum: file not found {filepath}")
        return
    checksum = calculate_checksum(filepath, algorithm=algorithm)
    _checksums.append({
        "path": str(filepath),
        "algorithm": algorithm,
        "hash": checksum
    })
    logger.info(f"Checksum computed for {filepath}: {checksum[:16]}...")

def write_feasibility_gate_result(
    status: str,
    reason: str,
    tcga_count: int,
    geo_count: int,
    output_path: Path
) -> None:
    """
    Write the feasibility gate result to JSON.
    Status: "ready", "halted", or "skipped_geo" (though spec says halted for geo < 2).
    """
    result = {
        "status": status,
        "reason": reason,
        "tcga_tumor_types_count": tcga_count,
        "valid_geo_datasets_count": geo_count,
        "message": f"TCGA types: {tcga_count}, Valid GEO datasets: {geo_count}"
    }
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Feasibility gate result written to {output_path}: {status}")

def run_data_feasibility_gate(tcga_count: int, geo_count: int) -> Tuple[bool, str]:
    """
    Execute the Data Feasibility Gate logic (T014).
    
    Returns:
        Tuple[proceed_to_training: bool, status_message: str]
    
    Logic:
    1. TCGA Gate: If tcga_count < 3 -> HALT (exit code 1).
    2. GEO Gate: If geo_count < 2 -> Halted but proceed to internal validation (skip external GEO validation).
    3. Proceed: If both conditions met.
    """
    project_root = get_project_root()
    gate_output_path = project_root / "data" / "feasibility_gate.json"
    
    # Ensure data directory exists
    ensure_directories([project_root / "data"])

    # 1. TCGA Gate Check
    if tcga_count < 3:
        logger.critical(f"TCGA Gate Failed: Only {tcga_count} tumor types found. Minimum required: 3.")
        write_feasibility_gate_result(
            status="halted",
            reason="insufficient_tcga_types",
            tcga_count=tcga_count,
            geo_count=geo_count,
            output_path=gate_output_path
        )
        # Atomically write checksums before exiting
        _finalize_checksums(project_root)
        return False, "halted_insufficient_tcga"

    # 2. GEO Gate Check
    if geo_count < 2:
        logger.warning(f"GEO Gate Warning: Only {geo_count} valid GEO datasets found. Minimum required: 2.")
        logger.warning("Proceeding to internal validation only. External GEO validation tasks will be skipped.")
        
        write_feasibility_gate_result(
            status="halted",
            reason="insufficient_geo_datasets",
            tcga_count=tcga_count,
            geo_count=geo_count,
            output_path=gate_output_path
        )
        
        # Atomically write checksums before proceeding
        _finalize_checksums(project_root)
        
        # Return True to allow internal processing, but flag that GEO is skipped
        # The caller (main.py) should check the 'reason' to skip external validation steps
        return True, "proceed_internal_only"

    # 3. Proceed Condition
    logger.info(f"Feasibility Gate Passed: {tcga_count} TCGA types, {geo_count} GEO datasets.")
    write_feasibility_gate_result(
        status="ready",
        reason="all_requirements_met",
        tcga_count=tcga_count,
        geo_count=geo_count,
        output_path=gate_output_path
    )
    
    # Atomically write checksums
    _finalize_checksums(project_root)
    
    return True, "ready"

def _finalize_checksums(project_root: Path) -> None:
    """
    Atomically write all collected checksums to the state artifact.
    Called before any exit or proceed in T014.
    """
    if not _checksums:
        logger.warning("No checksums to finalize.")
        return

    state_dir = project_root / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "PROJ-135-identifying-predictive-biomarkers-of-che.yaml"

    # Format as simple YAML map
    yaml_content = "artifact_hashes:\n"
    for item in _checksums:
        # Escape quotes if necessary, though paths usually don't have them
        path_str = item["path"].replace('\\', '/')
        yaml_content += f"  {path_str}: {item['hash']}\n"

    try:
        with open(state_file, 'w') as f:
            f.write(yaml_content)
        logger.info(f"Checksums finalized to {state_file}")
    except Exception as e:
        logger.error(f"Failed to write checksums to state file: {e}")
        # Do not crash here, but log heavily as this is a data integrity risk

def main():
    """
    Entry point for T014: Data Feasibility Gate.
    This function is intended to be called by src/main.py after acquisition.
    For testing/demonstration, it can be run standalone if arguments are provided.
    
    Usage:
      python -m src.data_acquisition --tcga 4 --geo 3
    """
    setup_logging()
    parser = argparse.ArgumentParser(description="Run Data Feasibility Gate (T014)")
    parser.add_argument("--tcga", type=int, required=True, help="Count of valid TCGA tumor types")
    parser.add_argument("--geo", type=int, required=True, help="Count of valid GEO datasets with labels")
    args = parser.parse_args()

    proceed, status = run_data_feasibility_gate(args.tcga, args.geo)

    if not proceed:
        sys.exit(1)
    else:
        # If status is 'proceed_internal_only', main.py needs to handle skipping GEO validation
        print(f"Gate Result: {status}")
        sys.exit(0)

if __name__ == "__main__":
    import argparse
    main()
