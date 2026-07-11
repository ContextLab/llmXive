"""
CLI entry point for the llmXive Code2LoRA follow-up pipeline.

Commands:
  generate   : Generate a repository-specific LoRA adapter using AST features.
  evaluate   : Evaluate adapter performance on RepoPeftBench tasks.
  sensitivity: Perform sensitivity analysis on feature complexity.
"""
import argparse
import sys
import time
import traceback
from pathlib import Path

# Import configuration and logging from existing modules
from utils.config import load_config, Config
from utils.logging import setup_logging, get_logger

def cmd_generate(args: argparse.Namespace, logger: any) -> int:
    """
    Execute the adapter generation pipeline.
    Delegates to code/hypernetwork/adapter_generator.py (T015).
    """
    logger.info("Starting adapter generation...")
    try:
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")

        # Validate data availability
        raw_data_path = Path(config.data_raw_dir)
        if not raw_data_path.exists():
            logger.error(f"Data directory {raw_data_path} does not exist. Run data download tasks first.")
            return 1

        # Import the actual generator implementation
        from hypernetwork.adapter_generator import main as generator_main
        
        # Prepare arguments for the generator
        gen_args = argparse.Namespace(
            repo_path=args.repo_path or config.repo_path,
            output_path=args.output or str(Path(config.adapters_dir) / "generated_adapter.safetensors"),
            config_path=args.config,
            log_level=args.log_level
        )
        
        # Execute generation
        return generator_main(gen_args)

    except Exception as e:
        logger.error(f"Generation failed: {e}")
        logger.error(traceback.format_exc())
        return 1

def cmd_evaluate(args: argparse.Namespace, logger: any) -> int:
    """
    Execute the evaluation pipeline.
    Delegates to code/evaluation/runner.py (T021).
    """
    logger.info("Starting adapter evaluation...")
    try:
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")

        # Validate data availability
        raw_data_path = Path(config.data_raw_dir)
        if not raw_data_path.exists():
            logger.error(f"Data directory {raw_data_path} does not exist. Run data download tasks first.")
            return 1

        # Import the actual evaluator implementation
        from evaluation.runner import main as evaluator_main
        
        # Prepare arguments for the evaluator
        eval_args = argparse.Namespace(
            adapter_path=args.adapter_path,
            benchmark=args.benchmark,
            config_path=args.config,
            log_level=args.log_level
        )
        
        # Execute evaluation
        return evaluator_main(eval_args)

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        logger.error(traceback.format_exc())
        return 1

def cmd_sensitivity(args: argparse.Namespace, logger: any) -> int:
    """
    Execute the sensitivity analysis pipeline.
    Delegates to code/evaluation/sensitivity.py (T030).
    """
    logger.info("Starting sensitivity analysis...")
    try:
        config = load_config(args.config)
        logger.info(f"Loaded config from {args.config}")

        # Validate data availability
        raw_data_path = Path(config.data_raw_dir)
        if not raw_data_path.exists():
            logger.error(f"Data directory {raw_data_path} does not exist. Run data download tasks first.")
            return 1

        # Import the actual sensitivity implementation
        from evaluation.sensitivity import main as sensitivity_main
        
        # Prepare arguments for sensitivity analysis
        sens_args = argparse.Namespace(
            feature_sets=args.feature_sets or config.sensitivity_feature_sets,
            config_path=args.config,
            log_level=args.log_level
        )
        
        # Execute sensitivity analysis
        return sensitivity_main(sens_args)

    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        logger.error(traceback.format_exc())
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="llmXive Code2LoRA Follow-up Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global arguments
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file (default: config.yaml)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to log file (default: stdout)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a repository-specific LoRA adapter")
    gen_parser.add_argument("--repo-path", type=str, help="Path to the repository to analyze")
    gen_parser.add_argument("--output", type=str, help="Output path for the adapter")

    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate adapter performance")
    eval_parser.add_argument("--adapter-path", type=str, help="Path to the adapter to evaluate")
    eval_parser.add_argument("--benchmark", type=str, default="repopeftbench", help="Benchmark dataset to use")

    # Sensitivity command
    sens_parser = subparsers.add_parser("sensitivity", help="Perform sensitivity analysis on feature complexity")
    sens_parser.add_argument("--feature-sets", type=str, nargs="+", help="Feature sets to analyze")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Setup logging
    logger = setup_logging(level=args.log_level, log_file=args.log_file)
    logger.info(f"Starting command: {args.command}")

    # Execute command
    if args.command == "generate":
        exit_code = cmd_generate(args, logger)
    elif args.command == "evaluate":
        exit_code = cmd_evaluate(args, logger)
    elif args.command == "sensitivity":
        exit_code = cmd_sensitivity(args, logger)
    else:
        logger.error(f"Unknown command: {args.command}")
        exit_code = 1

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
