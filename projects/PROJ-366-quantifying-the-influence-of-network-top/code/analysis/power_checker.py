"""
Statistical Power Check for Thermal Conductivity Analysis.

This module implements T035: Loads sample count N from processed conductivity data
(after outlier filtering), checks against statistical power requirements, and
writes a power analysis report.

Logic:
- If N < 2: Exit with code 1 (insufficient data for any analysis).
- If 2 <= N < 10: Log WARNING, write "INSUFFICIENT_POWER" status, but proceed.
- If N >= 10: Log INFO, write "SUFFICIENT_POWER" status.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import config utilities to locate paths and logging setup
from config import get_config, get_paths

# Setup logging via project config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def count_valid_samples(conductivity_dir: Path) -> int:
    """
    Count the number of valid thermal sample files in the conductivities directory.
    
    This mimics the filtering done by T024 (outlier detection) by assuming that
    any file present in this directory has already passed the exclusion criteria
    (or that the directory represents the final filtered set).
    
    Args:
        conductivity_dir: Path to data/processed/conductivities/
        
    Returns:
        Integer count of .pkl or .json files representing valid samples.
    """
    if not conductivity_dir.exists():
        logger.error(f"Conductivity directory does not exist: {conductivity_dir}")
        return 0
    
    # Look for serialized thermal samples (typically pickle or json)
    # Based on T025/T026, these are saved here.
    files = list(conductivity_dir.glob("*.pkl")) + list(conductivity_dir.glob("*.json"))
    
    # Filter out potential metadata files like convergence_report.json if they are mixed in
    # We expect sample files to be named like sample_*.pkl or similar, but a simple count
    # of data files is the primary metric here.
    # To be safe, we count files that are likely samples.
    # Assuming T025 saves individual sample objects.
    
    sample_count = 0
    for f in files:
        # Skip the convergence report if it's in the same folder
        if f.name == "convergence_report.json":
            continue
        sample_count += 1
        
    return sample_count

def write_power_analysis_report(output_path: Path, n: int, status: str, message: str) -> None:
    """
    Writes the power analysis result to a JSON file.
    
    Args:
        output_path: Path to write data/processed/model_outputs/power_analysis.json
        n: Sample count
        status: "SUFFICIENT_POWER" or "INSUFFICIENT_POWER"
        message: Human-readable explanation
    """
    report = {
        "sample_count": n,
        "status": status,
        "message": message,
        "threshold_min": 10,
        "threshold_abort": 2
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Power analysis report written to {output_path}")

def main() -> int:
    """
    Main entry point for T035.
    
    Returns:
        0 if successful (even if power is insufficient but N >= 2),
        1 if N < 2 (fatal error).
    """
    config = get_config()
    paths = get_paths(config)
    
    conductivities_dir = paths.get("conductivities", paths["data_root"] / "processed" / "conductivities")
    model_outputs_dir = paths.get("model_outputs", paths["data_root"] / "processed" / "model_outputs")
    
    logger.info(f"Scanning for samples in: {conductivities_dir}")
    
    n = count_valid_samples(conductivities_dir)
    logger.info(f"Found {n} valid samples in conductivities directory.")
    
    output_file = model_outputs_dir / "power_analysis.json"
    
    if n < 2:
        message = f"Fatal: Sample count (N={n}) is less than 2. Cannot proceed with analysis."
        write_power_analysis_report(output_file, n, "FATAL_INSUFFICIENT_DATA", message)
        logger.critical(message)
        return 1
    
    elif n < 10:
        message = f"Warning: Sample count (N={n}) is less than the statistical power target (10). Proceeding with proof-of-concept (N>=2)."
        write_power_analysis_report(output_file, n, "INSUFFICIENT_POWER", message)
        logger.warning(message)
        # Return 0 to allow downstream tasks (T030-T034) to proceed as per Plan/Spec conflict resolution
        return 0
    
    else:
        message = f"Success: Sample count (N={n}) meets the statistical power target (>=10)."
        write_power_analysis_report(output_file, n, "SUFFICIENT_POWER", message)
        logger.info(message)
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
