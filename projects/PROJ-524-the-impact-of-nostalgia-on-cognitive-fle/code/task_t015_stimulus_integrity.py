"""
Task T015: Stimulus Integrity Check
Validates stimulus files in data/stimuli/ against checksums in data/raw/metadata.json.
Runs ONLY if SIMULATION_MODE is False.
"""
import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

from config import get_config, get_env_bool, ensure_dirs
from utils import setup_logging, log_info, log_warning, log_error, compute_sha256

# Configure logging for this module
logger = setup_logging("task_t015_stimulus_integrity", level=logging.INFO)

def fetch_canonical_checksum_from_metadata(metadata_path: Path) -> Dict[str, str]:
    """
    Reads data/raw/metadata.json and extracts the 'stimuli_checksums' dictionary.
    Returns a mapping of filename -> expected_sha256.
    """
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    if 'stimuli_checksums' not in metadata:
        raise KeyError("Key 'stimuli_checksums' not found in metadata.json")
    
    return metadata['stimuli_checksums']

def compute_local_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    return compute_sha256(file_path)

def check_integrity(
    stimuli_dir: Path,
    expected_checksums: Dict[str, str],
    simulation_mode: bool
) -> Tuple[bool, Dict[str, Any]]:
    """
    Validates local stimulus files against expected checksums.
    
    Returns:
        Tuple[success, report_dict]
        - success: True if all checks pass, False otherwise.
        - report_dict: Contains details of the check.
    """
    report = {
        "simulation_mode": simulation_mode,
        "checks_performed": [],
        "errors": [],
        "status": "UNKNOWN"
    }

    if simulation_mode:
        log_info("SIMULATION_MODE is True. Skipping stimulus integrity check.")
        report["status"] = "SKIPPED_SIMULATION"
        report["checks_performed"].append("SKIPPED_STIMULUS_CHECK_SIMULATION")
        return True, report

    if not stimuli_dir.exists():
        msg = f"Stimuli directory does not exist: {stimuli_dir}"
        log_error(msg)
        report["errors"].append({"type": "ERR_STIMULUS_MISSING", "message": msg})
        report["status"] = "FAILED"
        return False, report

    missing_files = []
    corrupt_files = []
    
    for filename, expected_hash in expected_checksums.items():
        file_path = stimuli_dir / filename
        
        if not file_path.exists():
            msg = f"Stimulus file missing: {filename}"
            log_error(msg)
            missing_files.append(filename)
            report["errors"].append({"type": "ERR_STIMULUS_MISSING", "file": filename, "message": msg})
            report["checks_performed"].append(f"MISSING_{filename}")
            continue

        try:
            actual_hash = compute_local_checksum(file_path)
            report["checks_performed"].append(f"VERIFIED_{filename}")
            
            if actual_hash != expected_hash:
                msg = f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
                log_error(msg)
                corrupt_files.append(filename)
                report["errors"].append({"type": "ERR_STIMULUS_CORRUPT", "file": filename, "message": msg})
            else:
                log_info(f"Stimulus integrity verified: {filename}")
                report["checks_performed"].append(f"OK_{filename}")
        except Exception as e:
            msg = f"Error reading checksum for {filename}: {str(e)}"
            log_error(msg)
            report["errors"].append({"type": "ERR_STIMULUS_READ", "file": filename, "message": msg})

    if missing_files:
        log_error(f"Critical: {len(missing_files)} stimulus files missing.")
        report["status"] = "FAILED_MISSING"
        return False, report

    if corrupt_files:
        log_error(f"Critical: {len(corrupt_files)} stimulus files corrupted.")
        report["status"] = "FAILED_CORRUPT"
        return False, report

    log_info("All stimulus files verified successfully.")
    report["status"] = "PASSED"
    return True, report

def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Saves the integrity check report to data/results/stimulus_integrity_report.json.
    """
    ensure_dirs(output_path)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    log_info(f"Integrity report saved to {output_path}")

def main() -> int:
    """
    Main entry point for Task T015.
    """
    config = get_config()
    data_root = Path(config.get("data_root", "data"))
    stimuli_dir = data_root / "stimuli"
    metadata_path = data_root / "raw" / "metadata.json"
    output_path = data_root / "results" / "stimulus_integrity_report.json"
    
    simulation_mode = get_env_bool("SIMULATION_MODE", default=False)
    
    logger.info("Starting Task T015: Stimulus Integrity Check")
    logger.info(f"Simulation Mode: {simulation_mode}")

    try:
        # Fetch expected checksums
        expected_checksums = fetch_canonical_checksum_from_metadata(metadata_path)
        logger.info(f"Loaded {len(expected_checksums)} expected checksums from metadata.")
    except FileNotFoundError as e:
        log_error(f"Metadata file not found. Cannot proceed: {e}")
        # If metadata is missing, we cannot verify, but this might be expected in early dev.
        # However, per task spec, we should halt if we can't verify in non-sim mode.
        if not simulation_mode:
            return 1
        else:
            # In sim mode, just report skipped
            report = {
                "simulation_mode": True,
                "status": "SKIPPED_SIMULATION",
                "errors": [{"type": "ERR_METADATA_MISSING", "message": str(e)}]
            }
            save_report(report, output_path)
            return 0
    except KeyError as e:
        log_error(f"Metadata malformed: {e}")
        return 1

    success, report = check_integrity(stimuli_dir, expected_checksums, simulation_mode)

    save_report(report, output_path)

    if not success:
        logger.error("Stimulus integrity check FAILED. Halting pipeline.")
        return 1
    
    logger.info("Stimulus integrity check PASSED.")
    return 0

if __name__ == "__main__":
    exit(main())
