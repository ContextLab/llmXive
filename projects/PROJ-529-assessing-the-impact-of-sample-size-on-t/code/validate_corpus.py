import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from config import is_real_mode, is_simulation_mode, get_config
from utils.exceptions import DataAcquisitionError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

MIN_CORPUS_SIZE = 50  # SC-001 requirement

def count_meta_analyses(data_dir: Path) -> int:
    """
    Count the number of valid meta-analysis files in the raw data directory.
    
    Args:
        data_dir: Path to the directory containing raw meta-analysis data files.
        
    Returns:
        Integer count of valid meta-analysis files.
    """
    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return 0
    
    count = 0
    valid_extensions = {'.json', '.csv', '.parquet'}
    
    for file_path in data_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            # Skip simulation params file if it exists
            if file_path.name == 'simulation_params.json':
                continue
            
            # Basic validation: check if file is non-empty
            if file_path.stat().st_size > 0:
                count += 1
                logger.debug(f"Found valid meta-analysis file: {file_path.name}")
    
    logger.info(f"Total meta-analyses found in {data_dir}: {count}")
    return count

def write_report(report_path: Path, mode: str, count: int) -> None:
    """
    Write the validation report to the specified output path.
    
    Args:
        report_path: Path to the output JSON report file.
        mode: Either "real" or "simulation" indicating the data source mode.
        count: The number of meta-analyses counted.
    """
    report_dir = report_path.parent
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "mode": mode,
        "count": count,
        "target": MIN_CORPUS_SIZE,
        "meets_requirement": count >= MIN_CORPUS_SIZE,
        "timestamp": str(Path(report_path).parent.parent.name)  # Simple timestamp placeholder
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2)
    
    logger.info(f"Report written to {report_path}")

def main() -> None:
    """
    Main entry point for the corpus validation task (T012a).
    
    Logic:
    1. Determine if we are in real or simulation mode.
    2. If real mode, count files in data/raw/.
    3. If count < 50, log CRITICAL warning, switch to simulation mode, trigger T019.
    4. If count >= 50, log success.
    5. Write result to data/output/success_rate_report.json.
    """
    config = get_config()
    raw_data_dir = Path(config.get('raw_data_dir', 'data/raw'))
    output_report_path = Path(config.get('output_dir', 'data/output')) / 'success_rate_report.json'
    
    logger.info("Starting corpus validation (T012a)...")
    
    current_mode = "real" if is_real_mode() else "simulation"
    effective_count = 0
    
    if current_mode == "real":
        effective_count = count_meta_analyses(raw_data_dir)
        
        if effective_count < MIN_CORPUS_SIZE:
            logger.critical(
                f"Primary data requirement (FR-001) not met. "
                f"Found {effective_count} meta-analyses, required {MIN_CORPUS_SIZE}. "
                f"Switching to Simulation Mode."
            )
            # Trigger simulation fallback path (T019)
            # We call the fallback function from download.py
            try:
                from download import run_simulation_fallback
                run_simulation_fallback()
                current_mode = "simulation"
                # Re-count after simulation generation
                effective_count = count_meta_analyses(raw_data_dir)
            except Exception as e:
                logger.error(f"Failed to trigger simulation fallback: {e}")
                raise DataAcquisitionError(f"Failed to acquire real data and simulation fallback failed: {e}")
        else:
            logger.info(f"Success: Found {effective_count} meta-analyses (>= {MIN_CORPUS_SIZE}). Proceeding to T016.")
    else:
        # Already in simulation mode
        logger.info("Running in simulation mode. Counting generated data...")
        effective_count = count_meta_analyses(raw_data_dir)
    
    # Write the report
    write_report(output_report_path, current_mode, effective_count)
    
    if effective_count < MIN_CORPUS_SIZE and current_mode == "simulation":
        logger.warning(
            f"Even in simulation mode, count ({effective_count}) is below target ({MIN_CORPUS_SIZE}). "
            f"Proceeding with available data but results may be limited."
        )

if __name__ == "__main__":
    main()