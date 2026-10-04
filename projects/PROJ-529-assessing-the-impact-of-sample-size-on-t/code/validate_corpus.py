import os
import json
import logging
from pathlib import Path
from typing import Dict, Any
from config import is_real_mode, is_simulation_mode, get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def count_meta_analyses(raw_data_dir: Path) -> int:
    """
    Count the number of valid meta-analysis files in the raw data directory.
    
    Args:
        raw_data_dir: Path to the data/raw directory containing downloaded files
        
    Returns:
        int: Count of valid meta-analysis files
    """
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return 0
    
    count = 0
    # Look for common data file extensions
    valid_extensions = {'.csv', '.json', '.parquet', '.tsv'}
    
    for file_path in raw_data_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # Skip simulation params file if it exists (it's metadata, not data)
            if file_path.name == 'simulation_params.json':
                continue
            
            # Basic validation: check if file is not empty
            if file_path.stat().st_size > 0:
                count += 1
                logger.info(f"Found valid meta-analysis file: {file_path.name}")
            else:
                logger.warning(f"Skipping empty file: {file_path.name}")
    
    return count

def write_report(report_path: Path, mode: str, count: int) -> None:
    """
    Write the success rate report to JSON.
    
    Args:
        report_path: Path to the output report file
        mode: 'real' or 'simulation'
        count: Number of meta-analyses processed
    """
    report_data = {
        "mode": mode,
        "count": count,
        "target": 50,
        "meets_requirement": count >= 50
    }
    
    # Ensure output directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Report written to {report_path}")

def main() -> None:
    """
    Main entry point for corpus validation.
    
    This function:
    1. Counts meta-analyses in the raw data directory
    2. Validates against SC-001 (>=50 requirement)
    3. Logs appropriate warnings or success messages
    4. Writes the result to data/output/success_rate_report.json
    5. Triggers simulation fallback if count < 50
    """
    config = get_config()
    raw_data_dir = Path(config.get('raw_data_dir', 'data/raw'))
    output_dir = Path(config.get('output_dir', 'data/output'))
    report_path = output_dir / 'success_rate_report.json'
    
    logger.info(f"Validating corpus in {raw_data_dir}")
    
    count = count_meta_analyses(raw_data_dir)
    
    # Determine mode and log appropriate message
    if is_real_mode():
        if count >= 50:
            logger.info(f"SUCCESS: Found {count} meta-analyses (>= 50 target). Proceeding with real data.")
            mode = "real"
        else:
            logger.critical(
                f"Primary data requirement (FR-001) not met. "
                f"Found {count} meta-analyses, need >= 50. "
                "Switching to Simulation Mode."
            )
            mode = "simulation"
            # Trigger simulation fallback by calling the download module
            try:
                from download import run_simulation_fallback
                logger.info("Triggering simulation fallback (T019)...")
                run_simulation_fallback()
            except ImportError:
                logger.error("Could not import run_simulation_fallback from download.py")
            except Exception as e:
                logger.error(f"Simulation fallback failed: {e}")
    elif is_simulation_mode():
        logger.info(f"Simulation mode active. Count: {count}")
        mode = "simulation"
    else:
        # Default to real mode if not explicitly configured
        if count >= 50:
            logger.info(f"SUCCESS: Found {count} meta-analyses (>= 50 target).")
            mode = "real"
        else:
            logger.critical(
                f"Primary data requirement (FR-001) not met. "
                f"Found {count} meta-analyses, need >= 50. "
                "Switching to Simulation Mode."
            )
            mode = "simulation"
            try:
                from download import run_simulation_fallback
                run_simulation_fallback()
            except Exception as e:
                logger.error(f"Simulation fallback failed: {e}")
    
    # Write the report
    write_report(report_path, mode, count)
    
    logger.info(f"Validation complete. Mode: {mode}, Count: {count}")

if __name__ == "__main__":
    main()