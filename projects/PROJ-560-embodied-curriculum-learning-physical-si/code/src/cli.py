import argparse
import sys
import json
import os
import logging
from typing import List, Optional
from pathlib import Path

from .logging_config import setup_logging
from .data_loader import load_public_dataset, calculate_gain_scores, write_processed_data
from .synthetic_gen import SyntheticDataGenerator, generate_mapping_log
from .utils import set_seed

logger = logging.getLogger('proj_560')

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embodied Curriculum Learning Analysis Pipeline")
    parser.add_argument('--mode', type=str, required=True, choices=['secondary_analysis', 'synthetic'],
                        help='Mode of operation: secondary_analysis (load public) or synthetic (generate data)')
    parser.add_argument('--input', type=str, default=None,
                        help='Path to input dataset (CSV or JSON). Required for secondary_analysis if not using default.')
    parser.add_argument('--output', type=str, default='data/processed/results.csv',
                        help='Path to output processed data file.')
    parser.add_argument('--sweep_thresholds', type=str, default=None,
                        help='Comma-separated list of thresholds for sensitivity sweep.')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility.')
    parser.add_argument('--concept_definition', type=str, default=None,
                        help='Definition of the concept being analyzed.')
    parser.add_argument('--log-file', type=str, default='data/derivation_logs/pipeline.log',
                        help='Path to the log file.')
    return parser.parse_args()

def run_secondary_analysis(args: argparse.Namespace) -> None:
    logger.info("Running secondary analysis mode.")
    if not args.input:
        logger.error("Input path required for secondary analysis mode.")
        sys.exit(1)
    
    # Setup logging
    setup_logging(log_file=args.log_file)
    
    # Load data
    records = load_public_dataset(args.input, mode='secondary_analysis')
    
    # Calculate gains
    processed_records = calculate_gain_scores(records, log_file=Path('data/derivation_logs/skipped_records.log'))
    
    # Write output
    output_path = Path(args.output)
    write_processed_data(processed_records, output_path)
    
    logger.info("Secondary analysis complete.")

def run_synthetic_generation(args: argparse.Namespace) -> None:
    logger.info("Running synthetic generation mode.")
    
    # Setup logging
    setup_logging(log_file=args.log_file)
    
    set_seed(args.seed)
    
    generator = SyntheticDataGenerator(seed=args.seed)
    records = generator.generate()
    
    # Generate mapping log
    mapping_log_path = 'data/synthetic/mapping_log.json'
    generate_mapping_log(mapping_log_path, {
        "seed": args.seed,
        "n_samples": generator.n_samples,
        "mean_diff": generator.mean_diff,
        "std_dev": generator.std_dev
    })
    
    # Write synthetic data
    output_path = Path(args.output) if args.output else Path('data/synthetic/generated_data.csv')
    write_processed_data(records, output_path)
    
    logger.info("Synthetic generation complete. Mapping log saved to " + mapping_log_path)

def main():
    args = parse_args()
    
    # Initialize logging early to capture all messages
    setup_logging(log_file=args.log_file)
    logger.info(f"Starting pipeline with mode: {args.mode}")
    
    if args.mode == 'secondary_analysis':
        run_secondary_analysis(args)
    elif args.mode == 'synthetic':
        run_synthetic_generation(args)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)
    
    logger.info("Pipeline execution finished.")

if __name__ == "__main__":
    main()
