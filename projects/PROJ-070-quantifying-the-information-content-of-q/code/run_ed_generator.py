"""
Script to generate Exact Diagonalization dataset for User Story 1.

Generates wavefunctions for N=10 to N=20 Heisenberg and Ising models.
Outputs HDF5 files to data/raw/ directory.

Usage:
    python code/run_ed_generator.py
"""
import os
import sys
import argparse
from data_loader import generate_internal_dataset, validate_external_datasets
from logging_config import setup_logging, logger
from config import Config

def main():
    # Setup logging
    setup_logging()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='Generate ED wavefunction dataset')
    parser.add_argument('--model', type=str, default='heisenberg_1d',
                      choices=['heisenberg_1d', 'ising_1d'],
                      help='Model type to generate')
    parser.add_argument('--sizes', type=str, default='10,12,14,16,18,20',
                      help='Comma-separated list of system sizes')
    parser.add_argument('--output-dir', type=str, default='data/raw',
                      help='Output directory for HDF5 files')
    parser.add_argument('--seed', type=int, default=42,
                      help='Base random seed')
    parser.add_argument('--validate-external', action='store_true',
                      help='Validate external datasets before generation')
    
    args = parser.parse_args()
    
    # Parse system sizes
    system_sizes = [int(s.strip()) for s in args.sizes.split(',')]
    
    # Validate external datasets if requested
    if args.validate_external:
        try:
            validate_external_datasets()
        except RuntimeError as e:
            logger.warning(f"External dataset validation skipped: {e}")
            logger.info("Proceeding with internal generation")
    
    # Generate dataset
    logger.info(f"Generating {args.model} dataset for N={system_sizes}")
    
    try:
        output_files = generate_internal_dataset(
            model_type=args.model,
            system_sizes=system_sizes,
            output_dir=args.output_dir,
            seed_base=args.seed
        )
        
        if not output_files:
            logger.error("No files were generated. Check system size constraints.")
            sys.exit(1)
        
        logger.info(f"Successfully generated {len(output_files)} files:")
        for f in output_files:
            logger.info(f"  - {f}")
        
    except Exception as e:
        logger.error(f"Dataset generation failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
