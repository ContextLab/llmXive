import os
import sys
import logging
import subprocess
from typing import List
from utils import setup_logging

logger = logging.getLogger(__name__)

def run_script(script_name: str, args: List[str] = None) -> bool:
    """Run a Python script from the code directory."""
    script_path = os.path.join("code", script_name)
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)
    
    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with return code {e.returncode}")
        return False

def main():
    setup_logging("INFO")
    
    # Step 1: Ensure data exists (T011)
    logger.info("Ensuring dataset availability...")
    if not run_script("t011_ensure_data.py"):
        logger.error("Failed to ensure data availability.")
        sys.exit(1)
    
    # Step 2: Run baseline analysis (T012)
    logger.info("Running baseline analysis (T012)...")
    if not run_script("t012_run_baseline_analysis.py"):
        logger.error("Pipeline failed at t012_run_baseline_analysis.py")
        sys.exit(1)
    logger.info("Pipeline step T012 completed successfully.")

    # Step 3: Save cleaned datasets (T022)
    logger.info("Saving cleaned datasets (T022)...")
    if not run_script("t022_save_cleaned_datasets.py"):
        logger.error("Pipeline failed at t022_save_cleaned_datasets.py")
        sys.exit(1)
    logger.info("Pipeline step T022 completed successfully.")

    # Step 4: Re-analyze cleaned variants (T023)
    logger.info("Re-analyzing cleaned variants (T023)...")
    if not run_script("t023_reanalyze_cleaned_variants.py"):
        logger.error("Pipeline failed at t023_reanalyze_cleaned_variants.py")
        sys.exit(1)
    logger.info("Pipeline step T023 completed successfully.")

    # Step 5: Run comparison report (T027/T040)
    logger.info("Running comparison analysis (T027/T040)...")
    if not run_script("t027_run_comparison.py"):
        logger.error("Pipeline failed at t027_run_comparison.py")
        sys.exit(1)
    logger.info("Pipeline step T027/T040 completed successfully.")

    # Step 6: Generate visualizations (T034, T035)
    logger.info("Generating forest plot (T034)...")
    if not run_script("t034_generate_forest_plot.py"):
        logger.error("Pipeline failed at t034_generate_forest_plot.py")
        sys.exit(1)
    
    logger.info("Generating CI heatmap (T035)...")
    if not run_script("t035_generate_ci_heatmap.py"):
        logger.error("Pipeline failed at t035_generate_ci_heatmap.py")
        sys.exit(1)
    logger.info("Visualization steps completed successfully.")

    # Step 7: Final Report (T041)
    logger.info("Generating final report (T041)...")
    if not run_script("t041_generate_final_report.py"):
        logger.error("Pipeline failed at t041_generate_final_report.py")
        sys.exit(1)
    logger.info("Final report generated successfully.")

    logger.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()