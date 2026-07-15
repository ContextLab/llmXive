"""
API Contracts: Definitions for the CLI interface and function signatures.

This module documents the expected behavior of the pipeline's entry points
and ensures consistency between implementation and usage.
"""
import argparse
from typing import List, Optional, Callable, Any
from pathlib import Path

from ..logging_config import get_logger

logger = get_logger("contracts.api")

class CLIContract:
    """
    Contract for the command-line interface of the pipeline.
    
    Expected arguments:
    --run-all: Execute the full pipeline.
    --stage: Run a specific stage (e.g., 'ingestion', 'metrics', 'stats').
    --input-dir: Path to raw data.
    --output-dir: Path for processed outputs.
    --verbose: Enable debug logging.
    """
    
    REQUIRED_ARGS = {
        'run_all': {'action': 'store_true', 'help': 'Run the entire pipeline'},
        'stage': {'type': str, 'choices': ['ingestion', 'metrics', 'stats', 'viz'], 'help': 'Specific stage to run'},
        'input_dir': {'type': Path, 'help': 'Input data directory'},
        'output_dir': {'type': Path, 'help': 'Output directory for results'},
        'verbose': {'action': 'store_true', 'help': 'Enable verbose logging'}
    }
    
    @classmethod
    def build_parser(cls) -> argparse.ArgumentParser:
        """Constructs the argument parser according to the contract."""
        parser = argparse.ArgumentParser(
            description="llmXive Pipeline for Code Generation Impact Evaluation",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        
        parser.add_argument(
            '--run-all',
            **cls.REQUIRED_ARGS['run_all']
        )
        parser.add_argument(
            '--stage',
            **cls.REQUIRED_ARGS['stage']
        )
        parser.add_argument(
            '--input-dir',
            **cls.REQUIRED_ARGS['input_dir']
        )
        parser.add_argument(
            '--output-dir',
            **cls.REQUIRED_ARGS['output_dir']
        )
        parser.add_argument(
            '--verbose',
            **cls.REQUIRED_ARGS['verbose']
        )
        
        return parser
        
    @classmethod
    def validate_args(cls, args: argparse.Namespace) -> bool:
        """Validates that provided arguments meet contract requirements."""
        if not args.run_all and not args.stage:
            logger.error("CLIContract: Must specify either --run-all or --stage")
            return False
            
        if args.stage and not args.input_dir:
            logger.error("CLIContract: --input-dir is required for specific stages")
            return False
            
        return True

def validate_stage_function_signature(func: Callable, stage_name: str) -> bool:
    """
    Validates that a stage function matches the expected signature:
    func(input_dir: Path, output_dir: Path, config: Dict) -> bool
    """
    import inspect
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())
    
    expected_params = ['input_dir', 'output_dir']
    if not all(p in params for p in expected_params):
        logger.error(f"APIContract: Function {func.__name__} missing expected params {expected_params}")
        return False
        
    return True
