"""
Main CLI entry point for the llmXive pipeline.

Provides commands: generate, evaluate, sensitivity, and latency-compare.
"""
import argparse
import sys
import time
import traceback
from pathlib import Path
from utils.config import load_config, Config
from utils.logging import setup_logging, get_logger

# Import command modules
from hypernetwork.adapter_generator import main as cmd_generate_main
from evaluation.runner import main as cmd_evaluate_main
from evaluation.sensitivity import main as cmd_sensitivity_main
from utils.latency_monitor import main as cmd_baseline_latency_main
from utils.latency_ratio_comparator import main as cmd_latency_compare_main

logger = get_logger(__name__)

def cmd_generate(args: argparse.Namespace) -> int:
    """Execute the adapter generation pipeline."""
    logger.info("Starting adapter generation...")
    try:
        return cmd_generate_main()
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        traceback.print_exc()
        return 1

def cmd_evaluate(args: argparse.Namespace) -> int:
    """Execute the evaluation pipeline."""
    logger.info("Starting evaluation...")
    try:
        return cmd_evaluate_main()
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        traceback.print_exc()
        return 1

def cmd_sensitivity(args: argparse.Namespace) -> int:
    """Execute the sensitivity analysis pipeline."""
    logger.info("Starting sensitivity analysis...")
    try:
        return cmd_sensitivity_main()
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        traceback.print_exc()
        return 1

def cmd_baseline_latency(args: argparse.Namespace) -> int:
    """Measure baseline neural-encoder generation latency (T049a)."""
    logger.info("Measuring baseline generation latency...")
    try:
        return cmd_baseline_latency_main()
    except Exception as e:
        logger.error(f"Baseline latency measurement failed: {e}")
        traceback.print_exc()
        return 1

def cmd_latency_compare(args: argparse.Namespace) -> int:
    """Compute latency reduction ratio (T049b)."""
    logger.info("Computing latency reduction ratio...")
    try:
        return cmd_latency_compare_main()
    except Exception as e:
        logger.error(f"Latency comparison failed: {e}")
        traceback.print_exc()
        return 1

def main() -> int:
    """Main entry point with argparse CLI."""
    parser = argparse.ArgumentParser(
        description="llmXive: Automated Science Pipeline for Code2LoRA Extension",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser(
        "generate", 
        help="Generate AST-based LoRA adapter from repository features"
    )
    gen_parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml",
        help="Path to configuration file"
    )
    gen_parser.set_defaults(func=cmd_generate)
    
    # Evaluate command
    eval_parser = subparsers.add_parser(
        "evaluate", 
        help="Evaluate adapter performance on RepoPeftBench"
    )
    eval_parser.add_argument(
        "--adapter", 
        type=str, 
        required=True,
        help="Path to adapter file (.safetensors)"
    )
    eval_parser.add_argument(
        "--dataset", 
        type=str, 
        default="data/raw/repopeftbench",
        help="Path to dataset directory"
    )
    eval_parser.set_defaults(func=cmd_evaluate)
    
    # Sensitivity command
    sens_parser = subparsers.add_parser(
        "sensitivity", 
        help="Perform sensitivity analysis on feature subsets"
    )
    sens_parser.add_argument(
        "--config", 
        type=str, 
        default="config.yaml",
        help="Path to configuration file"
    )
    sens_parser.set_defaults(func=cmd_sensitivity)
    
    # Baseline latency command (T049a)
    baseline_parser = subparsers.add_parser(
        "baseline-latency", 
        help="Measure baseline neural-encoder generation latency"
    )
    baseline_parser.set_defaults(func=cmd_baseline_latency)
    
    # Latency compare command (T049b)
    compare_parser = subparsers.add_parser(
        "latency-compare", 
        help="Compute latency reduction ratio (AST vs Baseline)"
    )
    compare_parser.set_defaults(func=cmd_latency_compare)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    # Setup logging
    setup_logging()
    
    # Execute command
    return args.func(args)

if __name__ == "__main__":
    sys.exit(main())
