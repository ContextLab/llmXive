import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.pipelines.report import run_biome_driver_summary_pipeline
from src.config.constants import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Execute T029: Determine top driver per biome and calculate ranking stability.
    Reads from results/permanova_summary.csv and writes to results/biome_ranking_summary.csv.
    """
    config = get_config()
    results_dir = project_root / "results"
    
    if not results_dir.exists():
        logger.error("Results directory does not exist. Run previous analysis steps first.")
        sys.exit(1)

    permanova_file = results_dir / "permanova_summary.csv"
    output_file = results_dir / "biome_ranking_summary.csv"

    if not permanova_file.exists():
        logger.error(f"Input file {permanova_file} not found. Ensure T018/T022 have run.")
        sys.exit(1)

    logger.info(f"Running T029 analysis on {permanova_file}")
    
    try:
        passed = run_biome_driver_summary_pipeline(str(permanova_file), str(results_dir))
        if passed:
            logger.info("T029 PASSED: Standard deviation of top driver rank index <= 0.5")
        else:
            logger.warning("T029 FAILED: Standard deviation of top driver rank index > 0.5")
    except Exception as e:
        logger.error(f"Error running T029 analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
