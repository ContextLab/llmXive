import argparse
import sys
import os
import logging
from pathlib import Path
from checksum_raw_data import main as checksum_main
from config import load_config
import pandas as pd

def validate_data_source(config: dict) -> bool:
    """Validate that data source is configured."""
    if 'data_source' not in config:
        logging.error("ERROR: Data source not configured. Please specify a real Zenodo or UCI ID in data/config.yaml.")
        return False
    
    source_type = config['data_source'].get('source_type')
    source_id = config['data_source'].get('source_id')
    
    if not source_type or not source_id:
        logging.error("ERROR: Data source not configured. Please specify a real Zenodo or UCI ID in data/config.yaml.")
        return False
    
    return True

def check_dependency_energy_samples() -> bool:
    """Check if energy_samples.csv exists and is valid before running US2+ tasks."""
    input_file = 'data/derived/energy_samples.csv'
    
    if not os.path.exists(input_file):
        logging.error("ERROR: Dependency file data/derived/energy_samples.csv missing. Run US1 first.")
        return False
    
    # Validate file is not a test file
    if 'test_' in os.path.basename(input_file):
        logging.error("ERROR: Dependency file data/derived/energy_samples.csv appears to be a test file. Run US1 with real data first.")
        return False
    
    # Try to read and validate basic structure
    try:
        df = pd.read_csv(input_file)
        required_cols = ['particle_id', 'timestamp', 'E_trans', 'E_rot', 'E_pot', 'E_vib', 'pot_incomplete']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            logging.error(f"ERROR: Dependency file missing required columns: {missing}")
            return False
        if df.empty:
            logging.error("ERROR: Dependency file is empty.")
            return False
    except Exception as e:
        logging.error(f"ERROR: Cannot read dependency file: {e}")
        return False
    
    return True

def run_ingestion(args):
    """Run the ingestion stage."""
    from ingestion import main as ingestion_main
    # Call ingestion main with appropriate arguments
    ingestion_main()

def run_statistics(args):
    """Run the statistical analysis stage."""
    # Check dependency first
    if not check_dependency_energy_samples():
        sys.exit(1)
    
    from stats import main as stats_main
    stats_main()

def run_sensitivity(args):
    """Run the sensitivity analysis stage."""
    # Check dependency first
    if not check_dependency_energy_samples():
        sys.exit(1)
    
    from generate_sensitivity_report import main as sensitivity_main
    sensitivity_main()

def run_regression(args):
    """Run the regression analysis stage."""
    # Check dependency first
    if not check_dependency_energy_samples():
        sys.exit(1)
    
    from regression import main as regression_main
    regression_main()

def parse_args():
    parser = argparse.ArgumentParser(description='Granular Systems Analysis Pipeline')
    parser.add_argument('--stage', choices=['all', 'checksum_raw', 'hash_artifacts', 'ingest', 'stats', 'sensitivity', 'regression'],
                      default='all', help='Stage to run')
    parser.add_argument('--config', type=str, default='data/config.yaml', help='Path to config file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--sample-ratio', type=float, help='Sampling ratio for large datasets')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level for statistical tests')
    parser.add_argument('--thresholds', type=str, help='Comma-separated list of thresholds for sensitivity analysis')
    parser.add_argument('--data-source', type=str, help='Data source ID (Zenodo or UCI)')
    parser.add_argument('--local-only', action='store_true', help='Only use local data')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Load config
    config = load_config(args.config)
    
    # Validate data source if not in local-only mode
    if not args.local_only:
        if not validate_data_source(config):
            sys.exit(1)
    
    # Set sample ratio in config if provided
    if args.sample_ratio is not None:
        config['SAMPLE_SIZE'] = args.sample_ratio
    
    # Run stages
    if args.stage == 'all' or args.stage == 'checksum_raw':
        logging.info("Running checksum_raw stage...")
        checksum_main()
    
    if args.stage == 'all' or args.stage == 'hash_artifacts':
        logging.info("Running hash_artifacts stage...")
        from hash_artifacts import main as hash_main
        hash_main()
    
    if args.stage == 'all' or args.stage == 'ingest':
        logging.info("Running ingestion stage...")
        run_ingestion(args)
    
    if args.stage == 'all' or args.stage == 'stats':
        logging.info("Running statistical analysis stage...")
        run_statistics(args)
    
    if args.stage == 'all' or args.stage == 'sensitivity':
        logging.info("Running sensitivity analysis stage...")
        run_sensitivity(args)
    
    if args.stage == 'all' or args.stage == 'regression':
        logging.info("Running regression analysis stage...")
        run_regression(args)
    
    logging.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
