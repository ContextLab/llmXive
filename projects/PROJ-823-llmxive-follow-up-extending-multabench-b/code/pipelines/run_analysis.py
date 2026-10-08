"""
T024g: Updated run_analysis.py to fix log_info signature issue
"""
import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories, get_artifact_path, get_processed_path
from utils.logging import get_logger, log_info, log_error, log_warning

def run_pipeline(args):
    """Run the full statistical analysis pipeline."""
    logger = get_logger('run_analysis')
    
    # Fix: Use log_info with correct signature (logger is now handled internally)
    log_info("Starting full statistical analysis pipeline")
    
    ensure_directories()
    
    try:
        # Step 1: Validate baselines (T032a)
        log_info("Step 1: Validating GPU-tuned baselines")
        from pipelines.validate_baselines import main as validate_baselines_main
        validate_baselines_main()
        
        # Step 2: Extract baseline scalars (T032b)
        log_info("Step 2: Extracting baseline scalars")
        from pipelines.extract_baseline_scalars import main as extract_scalars_main
        extract_scalars_main()
        
        # Step 3: Run correlation analysis (T033, T031)
        log_info("Step 3: Running correlation analysis")
        from analysis.correlation import main as correlation_main
        correlation_main()
        
        # Step 4: Run FDR correction (T034)
        log_info("Step 4: Applying FDR correction")
        from pipelines.run_fdr_correction import main as fdr_main
        fdr_main()
        
        # Step 5: Run t-test analysis (T035)
        log_info("Step 5: Running t-test analysis")
        from analysis.t_test_analysis import main as ttest_main
        ttest_main()
        
        # Step 6: Generate correlation report (T036)
        log_info("Step 6: Generating correlation report")
        from pipelines.generate_correlation_report import main as report_main
        report_main()
        
        # Step 7: Power analysis (T057, T058)
        log_info("Step 7: Running power analysis")
        from analysis.correlation import main as power_analysis_main
        power_analysis_main()
        
        log_info("Statistical analysis pipeline completed successfully")
        return True
        
    except Exception as e:
        log_error(f"Pipeline failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Run full statistical analysis pipeline')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--epochs', type=int, default=15, help='Training epochs')
    args = parser.parse_args()
    
    success = run_pipeline(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
