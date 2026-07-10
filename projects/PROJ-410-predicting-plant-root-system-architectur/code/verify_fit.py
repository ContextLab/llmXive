"""
Verification script for the root system architecture prediction pipeline.

This module checks that required variables exist in the configuration and
data artifacts, logs any errors, and returns an appropriate status code.

It ensures that:
1. Required configuration variables are defined.
2. Expected data files exist and are non-empty.
3. Data schema matches expectations (basic structural check).
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.config import get_config
from code.download import verify_source_reachability

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_fit")

REQUIRED_CONFIG_VARS = [
    'DATA_RAW_DIR',
    'DATA_PROCESSED_DIR',
    'FIGURES_DIR',
    'RANDOM_SEED',
    'GENOTYPE_URL',
    'PHENOTYPE_URL'
]

REQUIRED_DATA_FILES = [
    'data/raw/accessions.csv',
    'data/raw/phenotypes.csv',
    'data/processed/unified_dataset.parquet'
]

def check_config_variables(config: Dict[str, Any]) -> List[str]:
    """Check if all required configuration variables exist."""
    errors = []
    for var in REQUIRED_CONFIG_VARS:
        if var not in config:
            errors.append(f"Missing config variable: {var}")
        elif config[var] is None:
            errors.append(f"Config variable {var} is None")
    return errors

def check_data_files(data_dirs: Dict[str, Path]) -> List[str]:
    """Check if required data files exist and are non-empty."""
    errors = []
    for file_path in REQUIRED_DATA_FILES:
        full_path = Path(file_path)
        if not full_path.exists():
            errors.append(f"Missing data file: {file_path}")
        elif full_path.stat().st_size == 0:
            errors.append(f"Empty data file: {file_path}")
    return errors

def check_schema_structure(data_dirs: Dict[str, Path]) -> List[str]:
    """Perform basic structural checks on data files."""
    errors = []
    unified_path = data_dirs.get('processed', Path('data/processed')) / 'unified_dataset.parquet'
    
    if unified_path.exists() and unified_path.stat().st_size > 0:
        try:
            import pandas as pd
            df = pd.read_parquet(unified_path)
            required_cols = ['accession', 'nutrient_condition', 'root_length']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors.append(f"Missing columns in unified dataset: {missing_cols}")
            if len(df) == 0:
                errors.append("Unified dataset is empty")
        except Exception as e:
            errors.append(f"Error reading unified dataset: {str(e)}")
    return errors

def verify_fit(config_path: Optional[str] = None, strict: bool = True) -> int:
    """
    Main verification function.
    
    Args:
        config_path: Optional path to config file. If None, uses defaults.
        strict: If True, return error code on any failure.
    
    Returns:
        0 if all checks pass, 1 otherwise.
    """
    logger.info("Starting verification process...")
    all_errors = []
    
    # Check configuration
    try:
        config = get_config(config_path)
        config_errors = check_config_variables(config)
        all_errors.extend(config_errors)
    except Exception as e:
        all_errors.append(f"Failed to load config: {str(e)}")
        config = {}
    
    # Check data files
    try:
        data_dirs = {
            'raw': Path(config.get('DATA_RAW_DIR', 'data/raw')),
            'processed': Path(config.get('DATA_PROCESSED_DIR', 'data/processed'))
        }
        file_errors = check_data_files(data_dirs)
        all_errors.extend(file_errors)
        
        # Schema checks
        schema_errors = check_schema_structure(data_dirs)
        all_errors.extend(schema_errors)
    except Exception as e:
        all_errors.append(f"Error checking data files: {str(e)}")
    
    # Check external source reachability if we have URLs
    if 'GENOTYPE_URL' in config and 'PHENOTYPE_URL' in config:
        try:
            reachable = verify_source_reachability(
                config['GENOTYPE_URL'],
                config['PHENOTYPE_URL']
            )
            if not reachable:
                all_errors.append("External data sources are not reachable")
        except Exception as e:
            all_errors.append(f"Error checking source reachability: {str(e)}")
    
    # Report results
    if all_errors:
        logger.error("Verification failed with the following errors:")
        for error in all_errors:
            logger.error(f"  - {error}")
        return 1
    else:
        logger.info("Verification successful. All checks passed.")
        return 0

def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Verify pipeline setup and data")
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Path to configuration file'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Return error code on any failure'
    )
    args = parser.parse_args()
    
    exit_code = verify_fit(
        config_path=args.config,
        strict=args.strict
    )
    sys.exit(exit_code)

if __name__ == "__main__":
    main()