"""
Script to execute Task T030: Save all plot artifacts to data/processed/plots/.

This script loads the correlation results from T024 and generates:
1. scatterplot_shannon_sleep.png: Scatter plot of Shannon diversity vs Sleep Efficiency
2. boxplot_sleep_quartile.png: Boxplot of Shannon diversity by sleep quartile

It relies on the implementation in src/viz.py which contains the actual plotting logic.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import load_config
from src.viz import save_all_plot_artifacts
from src.logging_config import setup_logger

def main():
    # Setup logging
    logger = setup_logger("T030_Plot_Saver", level=logging.INFO)
    logger.info("Starting Task T030: Saving plot artifacts...")

    # Load configuration
    try:
        config = load_config()
        data_url = config.get("DATA_URL")
        random_seed = config.get("RANDOM_SEED")
        log_level = config.get("LOG_LEVEL")
        logger.info(f"Configuration loaded. Seed: {random_seed}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Define paths
    plots_dir = project_root / "data" / "processed" / "plots"
    correlation_results_path = project_root / "data" / "processed" / "correlation_results.csv"
    cleaned_data_path = project_root / "data" / "processed" / "cleaned_microbiome_sleep.csv"

    # Ensure plots directory exists
    plots_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Plots directory ensured: {plots_dir}")

    # Check for required input files
    if not correlation_results_path.exists():
        logger.error(f"Correlation results file not found: {correlation_results_path}")
        logger.error("Task T024 must be completed before T030 can run.")
        sys.exit(1)
    
    if not cleaned_data_path.exists():
        logger.error(f"Cleaned data file not found: {cleaned_data_path}")
        logger.error("Task T016 must be completed before T030 can run.")
        sys.exit(1)

    logger.info("Input files verified. Generating plots...")

    # Execute the visualization logic
    try:
        # Call the function from viz.py which handles loading and plotting
        # It expects the paths relative to the project root or absolute
        save_all_plot_artifacts(
            correlation_results_path=str(correlation_results_path),
            cleaned_data_path=str(cleaned_data_path),
            output_dir=str(plots_dir),
            random_seed=random_seed
        )
        logger.info("Plot generation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Required data file missing during plot generation: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during plot generation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

    # Verification: Check that expected files exist
    expected_files = [
        "scatterplot_shannon_sleep.png",
        "boxplot_sleep_quartile.png"
    ]

    all_present = True
    for filename in expected_files:
        file_path = plots_dir / filename
        if file_path.exists():
            logger.info(f"Verified: {file_path} exists.")
        else:
            logger.error(f"Verification Failed: {file_path} does not exist.")
            all_present = False

    if all_present:
        logger.info("Task T030 completed successfully. All plot artifacts saved.")
        return 0
    else:
        logger.error("Task T030 failed: Some plot artifacts are missing.")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
