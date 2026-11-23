import argparse
import json
import sys
import os
import time
import signal
import logging

from src.utils.config import Config, load_config
from src.generators.logic_generator import main as generate_logic_main
from src.generators.grid_generator import main as generate_grid_main
from src.generators.test_generator import main as generate_test_main
from src.generators.data_writer import main as write_data_main
from src.analysis.validate_dataset import main as validate_main
from src.utils.checksums import main as checksum_main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_parser():
    parser = argparse.ArgumentParser(description="llmXive Co-Evolving Policy Distillation Pipeline")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate synthetic datasets')
    gen_parser.add_argument('--logic', type=int, default=100, help='Number of logic proofs')
    gen_parser.add_argument('--grid', type=int, default=50, help='Number of grid worlds')
    gen_parser.add_argument('--seed', type=int, default=42, help='Random seed')
    gen_parser.add_argument('--output', type=str, default='data/synthetic_dataset.json', help='Output file')

    # Run command (placeholder for training)
    run_parser = subparsers.add_parser('run', help='Run training conditions')
    run_parser.add_argument('--conditions', type=str, default='sequential,mixed,coevolving', help='Conditions to run')
    run_parser.add_argument('--generations', type=int, default=50, help='Number of generations')
    run_parser.add_argument('--runs-per-condition', type=int, default=30, help='Runs per condition')
    run_parser.add_argument('--seed', type=int, default=42, help='Random seed')

    # Analyze command (placeholder for analysis)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze results')
    analyze_parser.add_argument('--input', type=str, default='results/forgetting_metrics.csv', help='Input file')
    analyze_parser.add_argument('--output', type=str, default='results/statistical_report.json', help='Output file')

    # Pipeline command for T015c
    pipeline_parser = subparsers.add_parser('pipeline', help='Execute full data generation pipeline (T015c)')
    pipeline_parser.add_argument('--logic-count', type=int, default=100, help='Number of logic proofs')
    pipeline_parser.add_argument('--grid-count', type=int, default=50, help='Number of grid worlds')
    pipeline_parser.add_argument('--seed', type=int, default=42, help='Random seed')
    pipeline_parser.add_argument('--output-dir', type=str, default='data', help='Output directory')

    return parser

def execute_pipeline(args):
    """
    Execute the data generation pipeline: T011, T012, T013, T014, T015b.
    Outputs:
      - data/generated_proofs.json
      - data/generated_grids.json
      - data/test_instances.json
      - data/validation_report.json
    """
    logger.info(f"Starting pipeline with seed {args.seed}")
    config = load_config()

    # T011: Generate Logic Proofs
    logger.info("Step 1: Generating logic proofs...")
    logic_args = argparse.Namespace(
        count=args.logic_count,
        seed=args.seed,
        output=os.path.join(args.output_dir, 'generated_proofs.json')
    )
    generate_logic_main(logic_args)

    # T012: Generate Grid Worlds
    logger.info("Step 2: Generating grid worlds...")
    grid_args = argparse.Namespace(
        count=args.grid_count,
        seed=args.seed + 1,
        output=os.path.join(args.output_dir, 'generated_grids.json')
    )
    generate_grid_main(grid_args)

    # T013: Generate Test Instances
    logger.info("Step 3: Generating test instances...")
    test_args = argparse.Namespace(
        seed=args.seed + 2,
        output=os.path.join(args.output_dir, 'test_instances.json')
    )
    generate_test_main(test_args)

    # T014: Write Data (Checksums)
    logger.info("Step 4: Writing data and registering checksums...")
    write_args = argparse.Namespace(
        files=[
            os.path.join(args.output_dir, 'generated_proofs.json'),
            os.path.join(args.output_dir, 'generated_grids.json'),
            os.path.join(args.output_dir, 'test_instances.json')
        ],
        checksum_file=os.path.join(args.output_dir, 'checksums.json')
    )
    write_data_main(write_args)

    # T015b: Validate Dataset
    logger.info("Step 5: Validating dataset...")
    validate_args = argparse.Namespace(
        proofs=os.path.join(args.output_dir, 'generated_proofs.json'),
        grids=os.path.join(args.output_dir, 'generated_grids.json'),
        output=os.path.join(args.output_dir, 'validation_report.json')
    )
    validate_main(validate_args)

    logger.info("Pipeline completed successfully.")
    return 0

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.command == 'pipeline':
        sys.exit(execute_pipeline(args))
    elif args.command == 'generate':
        # Legacy generate command logic (simplified for CLI entry)
        generate_logic_main(args)
        generate_grid_main(args)
    elif args.command == 'run':
        logger.error("Training loop not implemented in this task scope.")
        sys.exit(1)
    elif args.command == 'analyze':
        logger.error("Analysis loop not implemented in this task scope.")
        sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)

if __name__ == '__main__':
    main()
