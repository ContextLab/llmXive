"""
Main CLI entry point for the Code2LoRA Hypernetwork pipeline.

Provides commands for:
- generate: Generate repository-specific adapters
- evaluate: Evaluate adapter performance
- sensitivity: Perform sensitivity analysis
- baseline_latency: Measure baseline generation latency
- latency_compare: Compare generation latencies

Implements graceful error handling for all custom exceptions from adapter_generator.py
"""
import argparse
import sys
import time
import traceback
from pathlib import Path
import logging

# Import from project modules
from utils.config import load_config, Config
from utils.logging import setup_logging, get_logger
from hypernetwork.adapter_generator import (
    generate_adapter,
    MemoryLimitError,
    CheckpointIncompatibilityError,
    AdapterGenerationError
)
from evaluation.runner import run_evaluation, main as eval_main
from evaluation.sensitivity import run_sensitivity_analysis, main as sensitivity_main
from evaluation.baseline_generator import main as baseline_main
from utils.latency_monitor import run_latency_analysis, main as latency_main
from utils.latency_ratio_comparator import run_latency_comparison, main as ratio_main

logger = get_logger(__name__)

def cmd_generate(args):
    """Generate repository-specific adapter command."""
    logger.info("Starting adapter generation...")
    
    try:
        config = load_config(args.config)
        
        result = generate_adapter(
            model_name_or_path=args.model,
            repo_path=args.repo,
            output_path=args.output,
            config=config,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr
        )
        
        # Save generation metadata
        import json
        metadata_path = args.output.replace('.pt', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Adapter generation successful. Metadata saved to {metadata_path}")
        return 0
        
    except MemoryLimitError as e:
        logger.error(f"ERROR: {e.code}: {e.message}")
        logger.error("Adapter generation aborted due to memory constraints.")
        return 1
        
    except CheckpointIncompatibilityError as e:
        logger.error(f"ERROR: {e.code}: {e.message}")
        logger.error("Adapter generation aborted due to checkpoint incompatibility.")
        return 1
        
    except AdapterGenerationError as e:
        logger.error(f"Adapter generation error: {e}")
        return 1
        
    except Exception as e:
        logger.error(f"Unexpected error during adapter generation: {e}")
        traceback.print_exc()
        return 1

def cmd_evaluate(args):
    """Evaluate adapter performance command."""
    logger.info("Starting adapter evaluation...")
    
    try:
        config = load_config(args.config)
        
        result = run_evaluation(
            adapter_path=args.adapter,
            data_path=args.data,
            output_path=args.output,
            config=config
        )
        
        logger.info(f"Evaluation completed. Results saved to {args.output}")
        return 0
        
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        traceback.print_exc()
        return 1

def cmd_sensitivity(args):
    """Perform sensitivity analysis command."""
    logger.info("Starting sensitivity analysis...")
    
    try:
        config = load_config(args.config)
        
        result = run_sensitivity_analysis(
            repo_path=args.repo,
            model_name=args.model,
            output_dir=args.output,
            config=config
        )
        
        logger.info(f"Sensitivity analysis completed. Results saved to {args.output}")
        return 0
        
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}")
        traceback.print_exc()
        return 1

def cmd_baseline_latency(args):
    """Measure baseline generation latency command."""
    logger.info("Measuring baseline generation latency...")
    
    try:
        result = run_latency_analysis()
        logger.info(f"Baseline latency measurement completed. Results saved to {result}")
        return 0
        
    except Exception as e:
        logger.error(f"Error during baseline latency measurement: {e}")
        traceback.print_exc()
        return 1

def cmd_latency_compare(args):
    """Compare generation latencies command."""
    logger.info("Comparing generation latencies...")
    
    try:
        result = run_latency_comparison()
        logger.info(f"Latency comparison completed. Results saved to {result}")
        return 0
        
    except Exception as e:
        logger.error(f"Error during latency comparison: {e}")
        traceback.print_exc()
        return 1

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Code2LoRA Hypernetwork Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate repository-specific adapter')
    gen_parser.add_argument('--model', type=str, default='TinyLlama-1.1B-Chat-hf',
                          help='Base model name or path')
    gen_parser.add_argument('--repo', type=str, required=True,
                          help='Path to repository to analyze')
    gen_parser.add_argument('--output', type=str, required=True,
                          help='Path to save generated adapter')
    gen_parser.add_argument('--config', type=str, default='config.yaml',
                          help='Path to configuration file')
    gen_parser.add_argument('--epochs', type=int, default=10,
                          help='Number of training epochs')
    gen_parser.add_argument('--batch-size', type=int, default=32,
                          help='Batch size for training')
    gen_parser.add_argument('--lr', type=float, default=1e-3,
                          help='Learning rate')
    gen_parser.set_defaults(func=cmd_generate)
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate adapter performance')
    eval_parser.add_argument('--adapter', type=str, required=True,
                           help='Path to adapter file')
    eval_parser.add_argument('--data', type=str, required=True,
                           help='Path to evaluation data')
    eval_parser.add_argument('--output', type=str, required=True,
                           help='Path to save results')
    eval_parser.add_argument('--config', type=str, default='config.yaml',
                           help='Path to configuration file')
    eval_parser.set_defaults(func=cmd_evaluate)
    
    # Sensitivity command
    sens_parser = subparsers.add_parser('sensitivity', help='Perform sensitivity analysis')
    sens_parser.add_argument('--repo', type=str, required=True,
                           help='Path to repository to analyze')
    sens_parser.add_argument('--model', type=str, default='TinyLlama-1.1B-Chat-hf',
                           help='Base model name or path')
    sens_parser.add_argument('--output', type=str, required=True,
                           help='Output directory for results')
    sens_parser.add_argument('--config', type=str, default='config.yaml',
                           help='Path to configuration file')
    sens_parser.set_defaults(func=cmd_sensitivity)
    
    # Baseline latency command
    baseline_parser = subparsers.add_parser('baseline_latency', help='Measure baseline generation latency')
    baseline_parser.add_argument('--config', type=str, default='config.yaml',
                               help='Path to configuration file')
    baseline_parser.set_defaults(func=cmd_baseline_latency)
    
    # Latency compare command
    compare_parser = subparsers.add_parser('latency_compare', help='Compare generation latencies')
    compare_parser.add_argument('--config', type=str, default='config.yaml',
                              help='Path to configuration file')
    compare_parser.set_defaults(func=cmd_latency_compare)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    
    # Execute command
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
