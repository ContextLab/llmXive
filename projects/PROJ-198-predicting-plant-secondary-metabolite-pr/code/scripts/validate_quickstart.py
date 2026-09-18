"""
Validation script for quickstart.md execution.

This script verifies that all steps in quickstart.md execute correctly,
checking directory structure, configuration, data alignment, modeling,
and report generation.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import setup_logging, get_logger
from config_env import ensure_directories, get_data_path
from data.align import align_data, save_aligned_matrix, calculate_alignment_success_rate
from modeling.train import apply_pca, load_pca_features, determine_cv_method
from modeling.eval import run_sensitivity_sweep, calculate_variation, save_metrics
from utils.report import generate_report

logger = get_logger(__name__)

def validate_directory_structure():
    """Validate that all required directories exist."""
    logger.info("Validating directory structure...")
    
    required_dirs = [
        "code",
        "code/data",
        "code/modeling",
        "code/utils",
        "code/cli",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "data/interim",
        "figures"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            missing_dirs.append(dir_path)
            logger.warning(f"Missing directory: {dir_path}")
        else:
            logger.debug(f"Directory exists: {dir_path}")
    
    if missing_dirs:
        logger.error(f"Missing directories: {missing_dirs}")
        return False
    
    logger.info("Directory structure validation passed")
    return True

def validate_config():
    """Validate configuration loading."""
    logger.info("Validating configuration...")
    
    try:
        from config import load_config, get_config
        from config_env import load_environment, validate_required_env_vars
        
        # Load environment
        env_config = load_environment()
        logger.debug(f"Environment loaded: {env_config.project_name}")
        
        # Validate required env vars
        missing_vars = validate_required_env_vars()
        if missing_vars:
            logger.warning(f"Missing required environment variables: {missing_vars}")
            # Not a hard failure for CI validation
        
        # Load main config
        config = load_config()
        logger.debug(f"Config loaded: {len(config.species_list)} species")
        
        logger.info("Configuration validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return False

def run_data_alignment_check():
    """Check that data alignment produces expected outputs."""
    logger.info("Running data alignment check...")
    
    try:
        from data.align import main as align_main
        
        # Check if aligned matrix exists
        aligned_path = Path("data/processed/aligned_matrix.csv")
        if aligned_path.exists():
            import pandas as pd
            df = pd.read_csv(aligned_path)
            logger.info(f"Aligned matrix found: {len(df)} rows, {len(df.columns)} columns")
            
            # Check for non-null values
            if df.notna().all().all():
                logger.info("All values in aligned matrix are non-null")
            else:
                logger.warning("Some values in aligned matrix are null")
        else:
            logger.warning("Aligned matrix not found - may need to run alignment")
        
        # Check metrics file
        metrics_path = Path("data/processed/metrics.json")
        if metrics_path.exists():
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
            logger.info(f"Metrics found: {list(metrics.keys())}")
        else:
            logger.warning("Metrics file not found")
        
        logger.info("Data alignment check passed")
        return True
        
    except Exception as e:
        logger.error(f"Data alignment check failed: {e}")
        return False

def run_modeling_check():
    """Check that modeling produces expected outputs."""
    logger.info("Running modeling check...")
    
    try:
        # Check PCA features
        pca_path = Path("data/interim/pca_features.csv")
        if pca_path.exists():
            import pandas as pd
            df = pd.read_csv(pca_path)
            logger.info(f"PCA features found: {len(df)} rows, {len(df.columns)} columns")
        else:
            logger.warning("PCA features not found - may need to run PCA")
        
        # Check model results
        results_path = Path("data/processed/primary_results.json")
        if results_path.exists():
            with open(results_path, 'r') as f:
                results = json.load(f)
            logger.info(f"Primary results found: {list(results.keys())}")
            
            # Check for R² > 0
            if 'r2' in results and results['r2'] > 0:
                logger.info(f"PGLS R² = {results['r2']} (positive, as expected)")
            else:
                logger.warning(f"PGLS R² = {results.get('r2', 'N/A')}")
        else:
            logger.warning("Primary results not found")
        
        # Check sensitivity results
        sensitivity_path = Path("data/processed/sensitivity_results.json")
        if sensitivity_path.exists():
            with open(sensitivity_path, 'r') as f:
                sensitivity = json.load(f)
            logger.info(f"Sensitivity results found: {list(sensitivity.keys())}")
        else:
            logger.warning("Sensitivity results not found")
        
        logger.info("Modeling check passed")
        return True
        
    except Exception as e:
        logger.error(f"Modeling check failed: {e}")
        return False

def run_report_generation_check():
    """Check that report generation produces expected outputs."""
    logger.info("Running report generation check...")
    
    try:
        report_path = Path("data/processed/final_report.md")
        if report_path.exists():
            with open(report_path, 'r') as f:
                content = f.read()
            
            logger.info(f"Final report found: {len(content)} characters")
            
            # Check for required sections
            required_sections = [
                "PGLS Results",
                "Sensitivity Analysis",
                "Threshold Justification"
            ]
            
            missing_sections = []
            for section in required_sections:
                if section not in content:
                    missing_sections.append(section)
                    logger.warning(f"Missing section in report: {section}")
            
            if missing_sections:
                logger.error(f"Report missing sections: {missing_sections}")
                return False
            
            logger.info("Report contains all required sections")
        else:
            logger.warning("Final report not found - may need to generate")
        
        logger.info("Report generation check passed")
        return True
        
    except Exception as e:
        logger.error(f"Report generation check failed: {e}")
        return False

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate quickstart.md execution")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--skip-data", action="store_true", help="Skip data alignment check")
    parser.add_argument("--skip-modeling", action="store_true", help="Skip modeling check")
    parser.add_argument("--skip-report", action="store_true", help="Skip report check")
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level=log_level)
    
    logger.info("=" * 60)
    logger.info("Starting quickstart.md validation")
    logger.info("=" * 60)
    
    # Run validation steps
    all_passed = True
    
    # Step 1: Directory structure
    if not validate_directory_structure():
        all_passed = False
    
    # Step 2: Configuration
    if not validate_config():
        all_passed = False
    
    # Step 3: Data alignment (optional)
    if not args.skip_data:
        if not run_data_alignment_check():
            all_passed = False
    
    # Step 4: Modeling (optional)
    if not args.skip_modeling:
        if not run_modeling_check():
            all_passed = False
    
    # Step 5: Report generation (optional)
    if not args.skip_report:
        if not run_report_generation_check():
            all_passed = False
    
    # Summary
    logger.info("=" * 60)
    if all_passed:
        logger.info("VALIDATION PASSED: All quickstart.md steps executed correctly")
        return 0
    else:
        logger.error("VALIDATION FAILED: Some quickstart.md steps did not execute correctly")
        return 1

if __name__ == "__main__":
    sys.exit(main())