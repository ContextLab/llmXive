"""
Task T037: Run quickstart.md validation.

This script validates the project's quickstart workflow by executing
the core pipeline steps in order and verifying that expected outputs
are generated.
"""
import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.download_esol import fetch_esol_dataset, save_raw_csv, main as download_main
from data.preprocess import load_and_preprocess, main as preprocess_main
from data.split import create_stratified_splits, save_split_indices, main as split_main
from models.baseline_rf import generate_morgan_fingerprint, load_processed_data, prepare_features_and_targets, train_random_forest, evaluate_model, main as rf_main
from setup_logging import setup_logger, log_training_metrics, log_exclusion_counts, main as logging_main
from config.seeds import set_seed, get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    if path.exists():
        logger.info(f"✓ {description} exists: {path}")
        return True
    else:
        logger.error(f"✗ {description} missing: {path}")
        return False

def validate_file_not_empty(path: Path, description: str, min_size: int = 100) -> bool:
    """Check if a file exists and has content."""
    if not path.exists():
        logger.error(f"✗ {description} missing: {path}")
        return False
    
    size = path.stat().st_size
    if size >= min_size:
        logger.info(f"✓ {description} exists and is non-empty ({size} bytes)")
        return True
    else:
        logger.error(f"✗ {description} too small: {size} bytes (min: {min_size})")
        return False

def validate_json_structure(path: Path, required_keys: List[str], description: str) -> bool:
    """Validate that a JSON file has the required structure."""
    if not path.exists():
        logger.error(f"✗ {description} missing: {path}")
        return False
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        missing_keys = [key for key in required_keys if key not in data]
        if not missing_keys:
            logger.info(f"✓ {description} has valid structure")
            return True
        else:
            logger.error(f"✗ {description} missing keys: {missing_keys}")
            return False
    except Exception as e:
        logger.error(f"✗ {description} invalid JSON: {e}")
        return False

def run_quickstart_validation(args: argparse.Namespace) -> Tuple[bool, Dict[str, Any]]:
    """
    Execute the quickstart validation workflow.
    
    Returns:
        Tuple of (success: bool, results: dict)
    """
    results = {
        'steps': [],
        'success': True,
        'errors': []
    }
    
    # Set random seed for reproducibility
    seed = get_seed()
    set_seed(seed)
    logger.info(f"Using random seed: {seed}")
    
    # Step 1: Download ESOL dataset
    logger.info("Step 1: Downloading ESOL dataset...")
    try:
        download_main()
        raw_csv = project_root / 'data' / 'raw' / 'esol_raw.csv'
        if validate_file_not_empty(raw_csv, "Raw ESOL CSV", min_size=1000):
            results['steps'].append('download_esol: passed')
        else:
            results['steps'].append('download_esol: failed')
            results['errors'].append('Raw ESOL CSV missing or empty')
            results['success'] = False
    except Exception as e:
        logger.error(f"ESOL download failed: {e}")
        results['steps'].append('download_esol: failed')
        results['errors'].append(f'ESOL download error: {str(e)}')
        results['success'] = False
    
    # Step 2: Preprocess data
    logger.info("Step 2: Preprocessing data...")
    if results['success']:
        try:
            preprocess_main()
            processed_dir = project_root / 'data' / 'processed'
            graphs_file = processed_dir / 'processed_graphs.json'
            if validate_file_not_empty(graphs_file, "Processed graphs JSON", min_size=1000):
                results['steps'].append('preprocess: passed')
            else:
                results['steps'].append('preprocess: failed')
                results['errors'].append('Processed graphs missing or empty')
                results['success'] = False
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            results['steps'].append('preprocess: failed')
            results['errors'].append(f'Preprocessing error: {str(e)}')
            results['success'] = False
    
    # Step 3: Split data
    logger.info("Step 3: Splitting data...")
    if results['success']:
        try:
            split_main()
            splits_dir = project_root / 'data' / 'processed'
            train_file = splits_dir / 'train_indices.json'
            val_file = splits_dir / 'val_indices.json'
            test_file = splits_dir / 'test_indices.json'
            
            all_valid = True
            for f, desc in [(train_file, 'Train indices'), (val_file, 'Val indices'), (test_file, 'Test indices')]:
                if not validate_file_not_empty(f, desc, min_size=10):
                    all_valid = False
            
            if all_valid:
                results['steps'].append('split: passed')
            else:
                results['steps'].append('split: failed')
                results['errors'].append('Split indices missing or empty')
                results['success'] = False
        except Exception as e:
            logger.error(f"Split failed: {e}")
            results['steps'].append('split: failed')
            results['errors'].append(f'Split error: {str(e)}')
            results['success'] = False
    
    # Step 4: Train Random Forest baseline
    logger.info("Step 4: Training Random Forest baseline...")
    if results['success']:
        try:
            rf_main()
            model_file = project_root / 'models' / 'baseline_rf.pkl'
            metrics_file = project_root / 'results' / 'baseline_metrics.json'
            
            model_valid = validate_file_not_empty(model_file, "Baseline RF model", min_size=100)
            metrics_valid = validate_json_structure(
                metrics_file, 
                ['r2', 'rmse', 'train_size', 'test_size'], 
                "Baseline metrics JSON"
            )
            
            if model_valid and metrics_valid:
                results['steps'].append('train_baseline: passed')
            else:
                results['steps'].append('train_baseline: failed')
                results['errors'].append('Baseline model or metrics missing/invalid')
                results['success'] = False
        except Exception as e:
            logger.error(f"Baseline training failed: {e}")
            results['steps'].append('train_baseline: failed')
            results['errors'].append(f'Baseline training error: {str(e)}')
            results['success'] = False
    
    # Step 5: Verify logging
    logger.info("Step 5: Verifying logging...")
    if results['success']:
        log_dir = project_root / 'data' / 'logs'
        log_files = list(log_dir.glob('*.log')) if log_dir.exists() else []
        
        if log_files:
            logger.info(f"✓ Found {len(log_files)} log files")
            results['steps'].append('logging: passed')
        else:
            logger.warning("⚠ No log files found (may be optional)")
            results['steps'].append('logging: skipped')
    
    # Summary
    logger.info("=" * 50)
    logger.info("Quickstart Validation Summary:")
    logger.info("=" * 50)
    
    for step in results['steps']:
        status = "✓" if "passed" in step or "skipped" in step else "✗"
        logger.info(f"  {status} {step}")
    
    if results['errors']:
        logger.warning("Errors encountered:")
        for error in results['errors']:
            logger.warning(f"  - {error}")
    
    logger.info(f"Overall: {'SUCCESS' if results['success'] else 'FAILURE'}")
    
    # Save validation report
    report_path = project_root / 'results' / 'quickstart_validation_report.json'
    try:
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation report saved to: {report_path}")
    except Exception as e:
        logger.error(f"Failed to save validation report: {e}")
    
    return results['success'], results

def main():
    parser = argparse.ArgumentParser(description='Validate quickstart workflow')
    parser.add_argument('--skip-download', action='store_true', 
                      help='Skip downloading ESOL dataset (assume already present)')
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success, results = run_quickstart_validation(args)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()