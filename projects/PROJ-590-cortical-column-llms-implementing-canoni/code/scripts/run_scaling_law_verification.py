"""
Script to run the scaling analysis and verify the output CSV.
This script is invoked by the run-book to ensure T049c is executed and verified.
"""
import sys
import logging
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.experiments.scaling import run_scaling_loop, write_scaling_results, DATA_RESULTS_DIR
from src.utils.checksum import calculate_sha256

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== Starting Scaling Law Verification ===")

    # 1. Run the scaling loop
    logger.info("Running scaling loop...")
    results = run_scaling_loop(base_columns=1, multipliers=[1, 2, 4])

    # 2. Write the CSV
    output_csv = str(DATA_RESULTS_DIR / "scaling_law.csv")
    logger.info(f"Writing results to {output_csv}")
    success = write_scaling_results(results, output_path=output_csv)

    if not success:
        logger.error("Failed to write or verify scaling_law.csv")
        sys.exit(1)

    # 3. Verify checksum (if hash_artifacts.sh is available, or just check existence)
    if not Path(output_csv).exists():
        logger.error(f"Output file {output_csv} does not exist after writing.")
        sys.exit(1)

    checksum = calculate_sha256(output_csv)
    logger.info(f"Generated checksum for scaling_law.csv: {checksum}")

    logger.info("=== Scaling Law Verification Completed Successfully ===")
    sys.exit(0)

if __name__ == "__main__":
    main()