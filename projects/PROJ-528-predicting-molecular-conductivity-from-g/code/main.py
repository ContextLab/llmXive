import os
import sys
import time
import json
import logging
import argparse

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.logging_config import setup_logging
from code.config import DATA_PATH
from code.data_loader import main as data_loader_main
from code.descriptors import main as descriptors_main
from code.model_training import main as model_training_main
from code.run_sensitivity_analysis import main as run_sensitivity
from code.feature_importance import main as feature_importance_main
from code.plotting import main as plotting_main
from code.analysis_summary import main as analysis_summary_main

logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary directories."""
    dirs = [
        os.path.join(DATA_PATH, "raw"),
        os.path.join(DATA_PATH, "processed"),
        os.path.join(DATA_PATH, "processed", "models_intermediate", "sensitivity"),
        os.path.join(DATA_PATH, "processed", "models_intermediate", "vif"),
        "logs",
        "figures"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    logger.info("Directories ensured.")

def ensure_sample_data():
    """Ensure sample data exists. If not, download from verified source."""
    raw_file = os.path.join(DATA_PATH, "raw", "smiles.csv")
    if not os.path.exists(raw_file):
        logger.info("Downloading sample data from verified source...")
        # This is handled by data_loader_main which uses the verified dataset
        pass
    return raw_file

def run_full_pipeline():
    """Run the full pipeline from data loading to analysis."""
    start_time = time.time()
    
    # 1. Ensure directories
    ensure_directories()
    
    # 2. Download/Load data
    logger.info("Step 1: Loading data...")
    data_loader_main()
    
    # 3. Compute descriptors
    logger.info("Step 2: Computing descriptors...")
    descriptors_main()
    
    # 4. Train models
    logger.info("Step 3: Training models...")
    model_training_main()
    
    # 5. Run sensitivity analysis (T032b + T032c)
    logger.info("Step 4: Running sensitivity analysis...")
    run_sensitivity()
    
    # 6. Feature importance
    logger.info("Step 5: Computing feature importance...")
    feature_importance_main()
    
    # 7. Plotting
    logger.info("Step 6: Generating plots...")
    plotting_main()
    
    # 8. Analysis summary
    logger.info("Step 7: Generating analysis summary...")
    analysis_summary_main()
    
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Pipeline completed in {duration:.2f} seconds.")
    
    return duration

def validate_outputs():
    """Validate that all expected outputs exist."""
    expected_files = [
        os.path.join(DATA_PATH, "raw", "smiles.csv"),
        os.path.join(DATA_PATH, "processed", "descriptors_base.csv"),
        os.path.join(DATA_PATH, "processed", "descriptors.csv"),
        os.path.join(DATA_PATH, "processed", "model_results.json"),
        os.path.join(DATA_PATH, "processed", "sensitivity_analysis.json"),
        os.path.join(DATA_PATH, "processed", "feature_importance.csv"),
        os.path.join(DATA_PATH, "processed", "analysis_summary.json"),
        os.path.join(DATA_PATH, "processed", "corr_plot_top5.png"),
    ]
    
    missing = []
    for f in expected_files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        logger.error(f"Missing output files: {missing}")
        return False
    
    logger.info("All expected outputs present.")
    return True

def main():
    """Main entry point."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Main pipeline runner")
    parser.add_argument("--pipeline", action="store_true", help="Run full pipeline")
    parser.add_argument("--validate", action="store_true", help="Validate outputs")
    args = parser.parse_args()
    
    if args.pipeline:
        run_full_pipeline()
    
    if args.validate:
        if not validate_outputs():
            sys.exit(1)
    
    if not args.pipeline and not args.validate:
        # Default: run pipeline
        run_full_pipeline()
        validate_outputs()

if __name__ == "__main__":
    main()
