import os
import sys
import logging
from pathlib import Path

# Add project root to path if running from code/
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.data.preprocessing import filter_by_snr_threshold
from src.utils.config import get_project_root, get_interim_data_dir, ensure_directories

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

DEFAULT_SNR_THRESHOLD_DB = 10.0

def main():
    """
    Execute the filtering engine with the default SNR threshold.
    
    Reads: data/interim/noise_mapped.csv (from T015)
    Writes: data/interim/filtered_snr.csv (Primary Output)
            data/interim/dropped_snr.csv (Exclusion Log)
    """
    logger.info("Starting T017b: Default SNR Filtering Execution")
    
    # Ensure directories exist
    ensure_directories()
    
    # Define paths
    project_root = get_project_root()
    interim_dir = get_interim_data_dir()
    
    input_file = interim_dir / "noise_mapped.csv"
    output_file = interim_dir / "filtered_snr.csv"
    dropped_file = interim_dir / "dropped_snr.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        logger.error("Prerequisite T015 (noise_mapped.csv) must be completed first.")
        raise FileNotFoundError(f"Missing input file: {input_file}")
    
    logger.info(f"Reading input from: {input_file}")
    logger.info(f"Applying default SNR threshold: {DEFAULT_SNR_THRESHOLD_DB} dB")
    
    # Execute filtering
    filtered_records, dropped_records = filter_by_snr_threshold(
        input_path=str(input_file),
        threshold_db=DEFAULT_SNR_THRESHOLD_DB,
        output_path=str(output_file),
        dropped_path=str(dropped_file)
    )
    
    logger.info(f"Filtering complete.")
    logger.info(f"  - Total input records: {filtered_records['total_input']}")
    logger.info(f"  - Records retained: {filtered_records['retained']}")
    logger.info(f"  - Records dropped: {dropped_records['dropped']}")
    logger.info(f"  - Output saved to: {output_file}")
    logger.info(f"  - Dropped log saved to: {dropped_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
