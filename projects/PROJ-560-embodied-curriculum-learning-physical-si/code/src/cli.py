import argparse
import sys
import json
import os
import logging
from typing import List, Optional

from .data_loader import main as data_loader_main
from .synthetic_gen import SyntheticDataGenerator
from .utils import set_seed
from .logging_config import setup_logging

logger = logging.getLogger(__name__)

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Args:
        args: List of arguments. If None, sys.argv[1:] is used.
        
    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Embodied Curriculum Learning Analysis Tool"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["secondary_analysis", "synthetic"],
        default="secondary_analysis",
        help="Operation mode: 'secondary_analysis' for public data, 'synthetic' for synthetic generation"
    )
    
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to input dataset (CSV or JSON). Required for secondary_analysis mode if public data is used."
    )
    
    parser.add_argument(
        "--sweep_thresholds",
        type=float,
        nargs="+",
        default=[0.01, 0.05, 0.10],
        help="Thresholds for sensitivity sweep analysis"
    )
    
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    parser.add_argument(
        "--n",
        type=int,
        default=100,
        help="Number of records to generate in synthetic mode"
    )
    
    parser.add_argument(
        "--mean_diff_embodied",
        type=float,
        default=5.0,
        help="Mean difference for embodied group in synthetic data"
    )
    
    parser.add_argument(
        "--mean_diff_static",
        type=float,
        default=2.0,
        help="Mean difference for static group in synthetic data"
    )
    
    return parser.parse_args(args)

def run_secondary_analysis(args: argparse.Namespace) -> None:
    """
    Run secondary analysis on public data.
    
    Args:
        args: Parsed command line arguments.
    """
    if not args.input:
        logger.error("Input file path is required for secondary_analysis mode")
        sys.exit(1)
    
    setup_logging()
    set_seed(args.seed)
    
    from .data_loader import load_public_dataset_with_fallback, calculate_gain_scores, write_processed_data
    
    records = load_public_dataset_with_fallback(
        file_path=args.input,
        n=args.n,
        seed=args.seed,
        mode="secondary_analysis"
    )
    
    gain_records = calculate_gain_scores(records)
    output_path = "data/processed/validated_fallback.csv"
    write_processed_data(gain_records, output_path)
    
    logger.info(f"Secondary analysis complete. Output: {output_path}")

def run_synthetic_generation(args: argparse.Namespace) -> None:
    """
    Run synthetic data generation.
    
    Args:
        args: Parsed command line arguments.
    """
    setup_logging()
    set_seed(args.seed)
    
    generator = SyntheticDataGenerator()
    records = generator.generate(
        n=args.n,
        seed=args.seed,
        mean_diff_embodied=args.mean_diff_embodied,
        mean_diff_static=args.mean_diff_static
    )
    
    # Write synthetic data
    from .data_loader import write_processed_data
    output_path = "data/synthetic/generated_data.csv"
    write_processed_data(records, output_path)
    
    # Write mapping log if required
    mapping_log_path = "data/synthetic/mapping_log.json"
    generator.write_mapping_log(mapping_log_path)
    
    logger.info(f"Synthetic generation complete. Data: {output_path}, Mapping: {mapping_log_path}")

def main() -> None:
    """Main entry point for CLI."""
    args = parse_args()
    
    if args.mode == "secondary_analysis":
        run_secondary_analysis(args)
    elif args.mode == "synthetic":
        run_synthetic_generation(args)
    else:
        logger.error(f"Unknown mode: {args.mode}")
        sys.exit(1)

if __name__ == "__main__":
    main()