"""
Quickstart Validation Script for PROJ-416.

This script executes the end-to-end pipeline as described in docs/quickstart.md
to verify that the entire flow works correctly on CI.

It performs the following steps:
1. Downloads data (or validates existing data)
2. Preprocesses fMRI data
3. Computes network metrics
4. Runs statistical analysis
5. Generates reports and plots
6. Validates that all expected output files exist
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import Config
from utils.logging import setup_logging

def log_section(title: str):
    """Log a section header."""
    logging.info(f"\n{'='*60}")
    logging.info(f" {title}")
    logging.info(f"{'='*60}\n")

def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    exists = path.exists()
    status = "✓" if exists else "✗"
    logging.info(f"{status} {description}: {path}")
    return exists

def run_pipeline_step(step_name: str, module_name: str, args: list = None):
    """Run a specific pipeline step."""
    log_section(f"Running: {step_name}")
    
    cmd = [sys.executable, "-m", module_name]
    if args:
        cmd.extend(args)
    
    logging.info(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per step
        )
        
        if result.returncode != 0:
            logging.error(f"Step '{step_name}' failed with code {result.returncode}")
            if result.stdout:
                logging.error("STDOUT:\n" + result.stdout)
            if result.stderr:
                logging.error("STDERR:\n" + result.stderr)
            return False
        
        if result.stdout:
            logging.info("Output:\n" + result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        
        return True
        
    except subprocess.TimeoutExpired:
        logging.error(f"Step '{step_name}' timed out after 1 hour")
        return False
    except Exception as e:
        logging.error(f"Step '{step_name}' raised exception: {str(e)}")
        return False

def validate_outputs():
    """Validate that all expected output files were created."""
    log_section("Validating Output Files")
    
    config = Config()
    expected_files = [
        (config.DATA_PROCESSED_DIR / "preprocessed_subjects.json", "Preprocessed subjects list"),
        (config.DATA_METRICS_DIR / "network_metrics.csv", "Network metrics CSV"),
        (config.DATA_METRICS_DIR / "statistical_results.csv", "Statistical results CSV"),
        (config.DATA_METRICS_DIR / "subject_info.json", "Subject info JSON"),
        (config.REPORTS_DIR / "results.md", "Final report"),
        (config.FIGURES_DIR / "scatter_post_vs_pre.png", "Scatter plot"),
        (config.FIGURES_DIR / "residuals.png", "Residual plot"),
        (config.LOGS_DIR / "preprocessing.log", "Preprocessing log"),
    ]
    
    all_exist = True
    for file_path, description in expected_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def main():
    """Main validation entry point."""
    # Setup logging
    log_file = project_root / "logs" / "quickstart_validation.log"
    setup_logging(log_file=log_file, level=logging.INFO)
    
    logging.info("Starting Quickstart Validation Pipeline")
    logging.info(f"Project Root: {project_root}")
    logging.info(f"Config: {Config()}")
    
    # Step 1: Download data (or validate existing)
    if not run_pipeline_step("Data Download", "data.download"):
        logging.error("Data download failed. Cannot proceed.")
        return 1
    
    # Step 2: Validate metadata
    if not run_pipeline_step("Metadata Validation", "data.validate"):
        logging.error("Metadata validation failed. Cannot proceed.")
        return 1
    
    # Step 3: Preprocess data
    if not run_pipeline_step("Data Preprocessing", "data.preprocess"):
        logging.error("Data preprocessing failed. Cannot proceed.")
        return 1
    
    # Step 4: Compute network metrics
    if not run_pipeline_step("Network Metrics", "analysis.network"):
        logging.error("Network metrics computation failed. Cannot proceed.")
        return 1
    
    # Step 5: Run statistical analysis
    if not run_pipeline_step("Statistical Analysis", "analysis.stats"):
        logging.error("Statistical analysis failed. Cannot proceed.")
        return 1
    
    # Step 6: Generate plots
    if not run_pipeline_step("Plot Generation", "analysis.plots"):
        logging.error("Plot generation failed. Cannot proceed.")
        return 1
    
    # Step 7: Generate report
    if not run_pipeline_step("Report Generation", "analysis.report"):
        logging.error("Report generation failed. Cannot proceed.")
        return 1
    
    # Step 8: Validate all outputs
    if not validate_outputs():
        logging.error("Output validation failed. Some expected files are missing.")
        return 1
    
    log_section("Quickstart Validation Complete")
    logging.info("✓ All pipeline steps completed successfully")
    logging.info("✓ All expected output files exist")
    logging.info("✓ Quickstart validation PASSED")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
