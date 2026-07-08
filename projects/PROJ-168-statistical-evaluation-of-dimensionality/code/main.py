"""
Main entry point for the Gene Expression Dimensionality Reduction Pipeline.

This script orchestrates the full workflow:
1. Invokes data_gap_resolver to verify dataset availability.
2. Sets pipeline mode (Aborted, Case-Study, or Full) based on findings.
3. Executes the Snakemake workflow with appropriate configuration flags.
"""

import sys
import os
import logging
import subprocess
from pathlib import Path
import json

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import Config
from data_gap_resolver import DataGapResolver, DatasetStatus

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(Path(project_root) / Config.LOG_FILE))
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Orchestrates the pipeline based on data availability.
    
    Logic:
    - 0 datasets: Abort with exit code 1, log "No Data".
    - 1 dataset: Switch to Case-Study mode (descriptive only, Fixed-Effects).
    - >1 dataset: Proceed with Fixed-Effects (N<=3) or Mixed-Effects (N>3).
    """
    logger.info("Starting pipeline initialization and data gap check...")
    
    # Initialize resolver
    resolver = DataGapResolver()
    status, found_datasets, missing_datasets = resolver.resolve()
    
    logger.info(f"Data gap resolution complete. Found: {len(found_datasets)}, Missing: {len(missing_datasets)}")
    
    # Determine pipeline mode and action
    n_datasets = len(found_datasets)
    
    if n_datasets == 0:
        logger.error("No Data: No valid raw count datasets found for the specified accessions.")
        # Abort with exit code 1
        sys.exit(1)
    
    # Determine mode
    if n_datasets == 1:
        mode = "CASE_STUDY"
        logger.info("Case-Study Mode: Exactly 1 dataset found. Switching to descriptive analysis (Fixed-Effects only).")
        # Ensure the config reflects this mode if needed downstream
        os.environ['PIPELINE_MODE'] = mode
        os.environ['STATS_MODEL'] = 'fixed_effects'
    else:
        if n_datasets <= 3:
            mode = "FIXED_EFFECTS"
            logger.info(f"Fixed-Effects Mode: {n_datasets} datasets found (N <= 3).")
            os.environ['PIPELINE_MODE'] = mode
            os.environ['STATS_MODEL'] = 'fixed_effects'
        else:
            mode = "MIXED_EFFECTS"
            logger.info(f"Mixed-Effects Mode: {n_datasets} datasets found (N > 3).")
            os.environ['PIPELINE_MODE'] = mode
            os.environ['STATS_MODEL'] = 'mixed_effects'
    
    # Save the data gap report to results (T044 dependency, but done here for flow)
    # Note: T044 is a separate task to formalize this, but we ensure the directory exists
    results_dir = Path(project_root) / Config.RESULTS_DIR
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "status": mode,
        "datasets_found": [d.accession for d in found_datasets],
        "datasets_missing": missing_datasets,
        "count": n_datasets
    }
    
    report_path = results_dir / "data_gap_report.json"
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Data gap report saved to {report_path}")
    
    # Proceed to Snakemake execution
    logger.info(f"Launching Snakemake workflow in {mode} mode...")
    
    snakemake_cmd = [
        "snakemake",
        "--snakefile", "Snakefile",
        "--cores", str(Config.N_CORES),
        "--rerun-incomplete",
        "--verbose"
    ]
    
    # Add specific flags based on mode if the Snakefile supports them
    # We pass the mode as a config override or environment variable if Snakefile reads it
    if mode == "CASE_STUDY":
        snakemake_cmd.extend(["--config", "mode=case_study"])
    
    try:
        result = subprocess.run(snakemake_cmd, cwd=project_root)
        if result.returncode != 0:
            logger.error(f"Pipeline execution failed with exit code {result.returncode}")
            sys.exit(result.returncode)
        else:
            logger.info("Pipeline completed successfully.")
            sys.exit(0)
            
    except FileNotFoundError:
        logger.error("Snakemake not found. Please ensure it is installed and in PATH.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()