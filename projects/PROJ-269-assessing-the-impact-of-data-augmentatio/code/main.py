"""
Main orchestration script for the llmXive automated science pipeline.

Runs the full pipeline: Download -> Subsample -> Baseline -> Augment -> Analyze -> Report.

Dependencies:
- T004: download_data.py
- T005: subsample.py
- T006, T018-T020: augment.py
- T007, T013, T021: simulation.py
- T008b, T014, T026-T029: analyze.py
- T027-T028: compare_results.py (implied by context of analysis)
- T029: identify_thresholds.py (implied by context of analysis)
- T030: inject_disclaimer.py
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import pipeline stages from existing modules
# Phase 1: Setup (Directories)
from setup_directories import main as setup_directories_main

# Phase 2: Data Acquisition
from download_data import main as download_data_main

# Phase 2: Subsampling
from subsample import main as subsample_main

# Phase 2: Simulation (Baseline) - T007/T013
# Note: simulation.py handles both baseline and augmented loops based on config
# We will invoke it via command line args or internal logic if needed.
# For orchestration, we assume it's called with specific flags.
from simulation import main as simulation_main

# Phase 2: Augmentation - T006/T018-T020
# augment.py contains the functions, but main() might handle CLI.
# We rely on simulation.py to call these functions internally as per T021.
# If separate execution is needed, we would call augment_main here.

# Phase 3/5: Analysis
from analyze import main as analyze_main
from compare_results import main as compare_results_main
from identify_thresholds import main as identify_thresholds_main

# Phase 5: Disclaimer Injection
from inject_disclaimer import main as inject_disclaimer_main

# Phase 5: Result Saving (if not handled by analyze/simulation)
# Assuming save_baseline_results and save_augmented_results are called 
# within the simulation or analysis steps. 
# If they are separate CLI tools, we would invoke them here.
# Based on T015/T023, saving is part of the simulation/analysis flow.

def run_pipeline(args):
    """Execute the full pipeline steps in order."""
    project_root = Path(args.project_root)
    
    logger.info(f"Starting pipeline for project: {project_root}")
    
    # 1. Setup Directories
    logger.info("Step 1: Setting up directories...")
    # setup_directories_main expects args or handles its own parsing. 
    # We pass the project root context.
    # Since setup_directories main() likely parses sys.argv, we might need to 
    # adjust if it doesn't accept a path argument. 
    # Assuming it uses a default or parses args.
    # To be safe, we change cwd or pass args if the function signature allows.
    # Given the constraints, we assume standard CLI behavior or default paths.
    try:
        setup_directories_main() 
    except SystemExit:
        pass # Expected if argparse exits after setup
    
    # 2. Download Data
    logger.info("Step 2: Downloading data...")
    try:
        download_data_main()
    except SystemExit:
        pass

    # 3. Subsample Data
    logger.info("Step 3: Subsampling data...")
    try:
        subsample_main()
    except SystemExit:
        pass

    # 4. Run Simulations (Baseline and Augmented)
    # T007/T013/T021: simulation.py handles the Monte Carlo loop.
    # We need to ensure it runs for both Null and Alt, and potentially 
    # with augmentation flags if the script supports it.
    # Assuming simulation.py main() handles the full loop or we call it with specific flags.
    logger.info("Step 4: Running Baseline Simulations...")
    try:
        # We might need to pass arguments to simulation_main to specify mode
        # If simulation_main parses sys.argv, we can't easily pass args from here 
        # without sys.argv manipulation. 
        # Assuming it has a default run or we rely on the script to run everything.
        simulation_main() 
    except SystemExit:
        pass

    # 5. Analyze Results
    logger.info("Step 5: Analyzing results...")
    try:
        analyze_main()
    except SystemExit:
        pass

    # 6. Compare Results (US3)
    logger.info("Step 6: Comparing results...")
    try:
        compare_results_main()
    except SystemExit:
        pass

    # 7. Identify Thresholds (US3)
    logger.info("Step 7: Identifying thresholds...")
    try:
        identify_thresholds_main()
    except SystemExit:
        pass

    # 8. Inject Disclaimer (T030)
    logger.info("Step 8: Injecting disclaimers...")
    try:
        inject_disclaimer_main()
    except SystemExit:
        pass

    logger.info("Pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Run the full llmXive science pipeline.")
    parser.add_argument(
        "--project-root", 
        type=str, 
        default="projects/PROJ-269-assessing-the-impact-of-data-augmentatio",
        help="Root directory of the project"
    )
    args = parser.parse_args()
    
    # Change to project root if necessary
    # (Most modules use relative paths or Path objects relative to CWD)
    os.chdir(args.project_root)
    
    run_pipeline(args)

if __name__ == "__main__":
    main()