import sys
import argparse
import time
import json
import logging
from pathlib import Path

# Add the 'code' directory to the path to allow imports from the project root structure
# This matches the execution context where scripts are run from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingest.fetch_structures import main as fetch_structures_main
from src.ingest.fetch_thermal import main as fetch_thermal_main
from src.cleaning.provenance_validator import main as provenance_main
from src.cleaning.temperature_normalize import main as normalize_main
from src.cleaning.clean_merge import main as merge_main
from src.descriptors.compute_descriptors import main as descriptors_main
from src.analysis.stratify import main as stratify_main
from src.analysis.correlation import main as correlation_main
from src.utils.sensitivity import main as sensitivity_main
from src.utils.validation import setup_logger
from src.ingest.track_checksums import main as checksums_main
from src.utils.metadata import main as metadata_main

def run_ingest_stage(seed: int = 42):
    """Execute the full data ingestion pipeline."""
    logger = setup_logger("ingest_stage")
    logger.info("Starting Ingest Stage")

    # 1. Fetch Structures
    logger.info("Fetching crystal structures...")
    fetch_structures_main()

    # 2. Fetch Thermal Data
    logger.info("Fetching thermal data...")
    fetch_thermal_main()

    # 3. Validate Provenance
    logger.info("Validating provenance...")
    provenance_main()

    # 4. Normalize Temperature
    logger.info("Normalizing temperature...")
    normalize_main()

    # 5. Merge and Clean
    logger.info("Merging datasets...")
    merge_main()

    logger.info("Ingest Stage Complete")

def run_descriptors_stage(seed: int = 42):
    """Execute descriptor computation."""
    logger = setup_logger("descriptors_stage")
    logger.info("Starting Descriptors Stage")

    # 1. Compute Descriptors
    logger.info("Computing structural descriptors...")
    descriptors_main()

    # 2. Stratify Data
    logger.info("Stratifying data by chemistry class...")
    stratify_main()

    logger.info("Descriptors Stage Complete")

def run_correlation_stage(seed: int = 42):
    """Execute correlation analysis."""
    logger = setup_logger("correlation_stage")
    logger.info("Starting Correlation Stage")

    # 1. Run Correlation
    logger.info("Running correlation analysis...")
    correlation_main()

    # 2. Run Sensitivity Analysis
    logger.info("Running sensitivity analysis...")
    # We pass specific p-values as required by the task spec
    import sys as _sys
    _sys.argv = ['src/utils/sensitivity.py', '--p-values', '0.01', '0.05', '0.1']
    sensitivity_main()

    logger.info("Correlation Stage Complete")

def run_regression_stage(seed: int = 42):
    """Execute regression modeling."""
    logger = setup_logger("regression_stage")
    logger.info("Starting Regression Stage")
    # Placeholder for regression logic if needed later
    logger.info("Regression Stage Complete")

def main():
    parser = argparse.ArgumentParser(description="llmXive Research Pipeline Runner")
    parser.add_argument('--stage', type=str, required=True,
                        choices=['ingest', 'descriptors', 'correlation', 'regression', 'full'],
                        help='Pipeline stage to execute')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    args = parser.parse_args()

    setup_logger("pipeline_runner", level=logging.INFO)

    start_time = time.time()

    if args.stage == 'ingest':
        run_ingest_stage(args.seed)
    elif args.stage == 'descriptors':
        run_descriptors_stage(args.seed)
    elif args.stage == 'correlation':
        run_correlation_stage(args.seed)
    elif args.stage == 'regression':
        run_regression_stage(args.seed)
    elif args.stage == 'full':
        run_ingest_stage(args.seed)
        run_descriptors_stage(args.seed)
        run_correlation_stage(args.seed)
        # run_regression_stage(args.seed) # Optional based on full scope

    end_time = time.time()
    logging.info(f"Pipeline execution completed in {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
