import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import existing utilities from the project API surface
from utils.exceptions import DataAcquisitionError
from download import run_fallback_simulation, generate_synthetic_meta_analyses
from subsample import load_meta_analyses
from config import get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
DATA_OUTPUT_DIR = Path("data/output")
TARGET_COUNT = 50  # SC-001 requirement

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.warning(f"Could not calculate checksum for {file_path}: {e}")
        return "error"

def validate_data_integrity(raw_files: List[Path]) -> Dict[str, Any]:
    """
    Verify downloaded/generated data integrity and checksums.
    Returns a dict with validation results per file.
    """
    results = {
        "total_files": len(raw_files),
        "valid_files": 0,
        "invalid_files": 0,
        "details": []
    }

    for file_path in raw_files:
        if not file_path.exists():
            results["invalid_files"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": "missing",
                "checksum": None
            })
            continue

        try:
            # Basic integrity check: file size > 0
            if file_path.stat().st_size == 0:
                results["invalid_files"] += 1
                results["details"].append({
                    "file": str(file_path),
                    "status": "empty",
                    "checksum": None
                })
                continue

            # Calculate checksum
            checksum = calculate_file_checksum(file_path)
            
            # Attempt to parse as JSON to verify structure
            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if not isinstance(data, (dict, list)):
                        results["invalid_files"] += 1
                        results["details"].append({
                            "file": str(file_path),
                            "status": "invalid_json_structure",
                            "checksum": checksum
                        })
                        continue
            
            results["valid_files"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": "valid",
                "checksum": checksum,
                "size_bytes": file_path.stat().st_size
            })

        except json.JSONDecodeError:
            results["invalid_files"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": "invalid_json",
                "checksum": None
            })
        except Exception as e:
            results["invalid_files"] += 1
            results["details"].append({
                "file": str(file_path),
                "status": f"error: {str(e)}",
                "checksum": None
            })

    return results

def aggregate_success_rate(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate the success rate of meta-analyses processed against the >=50 target.
    Returns the summary report structure.
    """
    actual_processed = validation_results.get("valid_files", 0)
    success_rate = (actual_processed / TARGET_COUNT) if TARGET_COUNT > 0 else 0.0
    
    # Determine mode based on file content or existence
    mode = "simulation"
    simulation_params_path = DATA_RAW_DIR / "simulation_params.json"
    
    if simulation_params_path.exists():
        try:
            with open(simulation_params_path, 'r') as f:
                params = json.load(f)
                # If simulation params exist, we are in simulation mode
                mode = "simulation"
        except Exception:
            mode = "simulation"
    else:
        # Check if we have real data files (non-simulation)
        real_data_files = [f for f in validation_results.get("details", []) 
                         if "simulation" not in f.get("file", "").lower()]
        if len(real_data_files) > 0:
            mode = "real"
    
    # If actual processed is 0, default to simulation mode if no real data found
    if actual_processed == 0:
        mode = "simulation"

    return {
        "total_target": TARGET_COUNT,
        "actual_processed": actual_processed,
        "success_rate": round(success_rate, 4),
        "mode": mode,
        "validation_summary": {
            "total_files_scanned": validation_results.get("total_files", 0),
            "valid_files": validation_results.get("valid_files", 0),
            "invalid_files": validation_results.get("invalid_files", 0)
        }
    }

def ensure_output_directories():
    """Ensure all required output directories exist."""
    DATA_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

def main():
    """
    Main validation function for T017.
    Verifies data integrity, calculates success rate, and writes report.
    """
    logger.info("Starting data validation for T017...")
    
    # Ensure directories exist
    ensure_output_directories()

    # Collect all raw data files
    raw_files = []
    if DATA_RAW_DIR.exists():
        raw_files = list(DATA_RAW_DIR.glob("*"))
        # Filter for relevant data files
        raw_files = [f for f in raw_files if f.is_file() and not f.name.startswith('.')]
    
    logger.info(f"Found {len(raw_files)} files in data/raw/")

    # Validate data integrity
    validation_results = validate_data_integrity(raw_files)
    logger.info(f"Validation complete: {validation_results['valid_files']}/{validation_results['total_files']} files valid")

    # Aggregate success rate
    success_report = aggregate_success_rate(validation_results)
    
    # Write report to data/output/success_rate_report.json
    output_path = DATA_OUTPUT_DIR / "success_rate_report.json"
    with open(output_path, 'w') as f:
        json.dump(success_report, f, indent=2)
    
    logger.info(f"Success rate report written to {output_path}")
    logger.info(f"Mode: {success_report['mode']}, Processed: {success_report['actual_processed']}/{success_report['total_target']}")

    # Log critical warning if target not met
    if success_report['actual_processed'] < TARGET_COUNT:
        logger.warning(f"CRITICAL: Primary data requirement (FR-001) not met. "
                     f"Actual: {success_report['actual_processed']}, Target: {TARGET_COUNT}. "
                     f"Switching to Simulation Mode.")

    return success_report

if __name__ == "__main__":
    main()
