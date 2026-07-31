"""
Main pipeline orchestrator for llmXive follow-up project.
Executes all phases in sequence and generates required artifacts.
"""
import os
import sys
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

# Add code directory to path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import load_config_from_file, ensure_directories
from parser import main as run_parser
from entropy import main as run_entropy
from splitter import main as run_splitter
from ablation import main as run_ablation
from classifier import main as run_classifier
from run_dynamic_simulation import main as run_dynamic_sim
from run_random_baseline import main as run_random_baseline
from baseline_static_runner import main as run_static_baseline
from generate_baseline_comparison import main as run_baseline_comparison
from token_consistency_checker import main as run_token_consistency
from stats import main as run_stats
from divergence_checker import main as run_divergence_check
from check_sample_size import main as run_sample_size_check
from t008d_ablation_failure_handler import main as run_ablation_failure_handler
from proxy_validation import main as run_proxy_validation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_full_pipeline():
    """Execute the full research pipeline."""
    logger.info("Starting FULL pipeline execution.")
    start_time = datetime.now()
    
    try:
        # Ensure directories
        ensure_directories()
        
        # Phase 1: Data Ingestion and Parsing
        logger.info("Phase 1: Parsing raw trajectories")
        # T005b and T005c should have run already to populate data/raw/
        # T006a: Parse trajectories
        run_parser()
        
        # Phase 2: Feature Extraction
        logger.info("Phase 2: Entropy calculation")
        # T006b: Calculate entropy
        run_entropy()
        
        # T014a: Split data
        logger.info("Phase 3: Data splitting")
        run_splitter()
        
        # Check sample size
        logger.info("Checking sample size...")
        run_sample_size_check()
        
        # T008: Ablation study (if not failed)
        logger.info("Phase 4: Ablation study")
        ablation_success = False
        try:
            run_ablation()
            ablation_success = True
        except Exception as e:
            logger.error(f"Ablation study failed: {e}")
            ablation_success = False
        
        # T008d: Handle ablation failure if needed
        if not ablation_success:
            logger.info("Handling ablation failure...")
            run_ablation_failure_handler()
        
        # T014: Proxy validation
        logger.info("Phase 5: Proxy validation")
        run_proxy_validation()
        
        # T009: Train classifier
        logger.info("Phase 6: Training classifier")
        run_classifier()
        
        # Phase 7: Simulations
        logger.info("Phase 7: Running simulations")
        
        # T017: Dynamic simulation
        logger.info("Running dynamic simulation...")
        run_dynamic_sim()
        
        # T019: Static baseline
        logger.info("Running static baseline...")
        run_static_baseline()
        
        # T020: Random baseline
        logger.info("Running random baseline...")
        run_random_baseline()
        
        # T022: Generate baseline comparison
        logger.info("Generating baseline comparison...")
        run_baseline_comparison()
        
        # T023: Token consistency check
        logger.info("Checking token consistency...")
        run_token_consistency()
        
        # T024 & T025a: Statistical tests
        logger.info("Running statistical analysis...")
        run_stats()
        
        # T050: Divergence check
        logger.info("Running divergence check...")
        run_divergence_check()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Pipeline completed successfully in {duration:.2f} seconds.")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_dry_run_pipeline():
    """Execute a dry run to check dependencies and configuration."""
    logger.info("Starting DRY RUN pipeline execution.")
    try:
        ensure_directories()
        logger.info("Directory structure validated.")
        
        # Check for required input files
        raw_data = Path("data/raw/agenticsts_trajectories.jsonl")
        if raw_data.exists():
            logger.info(f"Found raw data: {raw_data}")
        else:
            logger.warning(f"Raw data not found: {raw_data}")
        
        logger.info("Dry run completed.")
        return True
    except Exception as e:
        logger.error(f"Dry run failed: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="llmXive Follow-up Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Run dependency check only")
    parser.add_argument("--full", action="store_true", help="Run full pipeline")
    args = parser.parse_args()
    
    if args.dry_run:
        success = run_dry_run_pipeline()
        sys.exit(0 if success else 1)
    else:
        # Default to full pipeline if no args provided
        success = run_full_pipeline()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()