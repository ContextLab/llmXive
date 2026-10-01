"""
Gate enforcement module for the llmXive project.

This module handles the validation of proxy correlations and other gates
that must pass before downstream tasks can execute.
"""
import os
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from config import get_mode, is_ci_mode, is_research_mode, get_path, ensure_paths_exist
from utils.logger import setup_project_logger, log_error, log_fatal

logger = setup_project_logger("eval_gate")

def load_validation_result(file_path: str = None) -> Dict[str, Any]:
    """Load the proxy validation result JSON."""
    if file_path is None:
        file_path = get_path("results", "proxy_validation.json")
    
    if not os.path.exists(file_path):
        log_fatal(f"Validation result file not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    logger.info(f"Loading validation result from: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def save_validation_result(file_path: str, data: Dict[str, Any]) -> None:
    """Save validation result to JSON."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    logger.info(f"Saving validation result to: {file_path}")
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def run_proxy_correlation_gate(
    validation_file: Optional[str] = None,
    output_file: Optional[str] = None
) -> bool:
    """
    Run the proxy correlation gate check.
    
    This function:
    1. Loads the validation result from T035
    2. Checks if gate_status is 'BLOCKED'
    3. If BLOCKED and in RESEARCH mode, raises SystemExit
    4. If BLOCKED and in CI mode, logs warning but allows execution
    
    Args:
        validation_file: Path to proxy_validation.json
        output_file: Path to updated validation file (optional)
    
    Returns:
        bool: True if gate passed, False if blocked (but allowed in CI)
    """
    if validation_file is None:
        validation_file = get_path("results", "proxy_validation.json")
    
    logger.info("Running proxy correlation gate check...")
    
    try:
        result = load_validation_result(validation_file)
    except FileNotFoundError:
        log_fatal("Proxy validation file not found. Run T035 first.")
        raise
    
    gate_status = result.get('gate_status', 'UNKNOWN')
    mode = result.get('mode', get_mode())
    
    logger.info(f"  Gate status: {gate_status}")
    logger.info(f"  Mode: {mode}")
    
    if gate_status == 'BLOCKED':
        if mode == 'RESEARCH':
            log_error("=" * 60)
            log_error("GATE BLOCKED: Proxy correlation r < 0.7 in Research Mode.")
            log_error("  Downstream training tasks cannot proceed.")
            log_error("=" * 60)
            raise SystemExit(1)
        else:
            logger.warning("Gate blocked, but in CI mode. Allowing execution to continue.")
            logger.warning("  This is expected behavior for CI with decoupled synthetic scores.")
            return False
    elif gate_status == 'PASSED':
        logger.info("Gate PASSED. Proceeding with downstream tasks.")
        return True
    elif gate_status == 'EXPECTED_LOW_CORRELATION':
        logger.info("Gate status: EXPECTED_LOW_CORRELATION (CI mode).")
        logger.info("  Continuing execution as expected.")
        return True
    else:
        log_error(f"Unknown gate status: {gate_status}")
        raise ValueError(f"Unknown gate status: {gate_status}")

def main():
    """CLI entry point for the gate module."""
    parser = argparse.ArgumentParser(description="Gate enforcement for llmXive project")
    parser.add_argument('--command', type=str, default='check',
                      choices=['check'],
                      help='Command to run (default: check)')
    parser.add_argument('--validation-file', type=str,
                      help='Path to proxy_validation.json')
    parser.add_argument('--output-file', type=str,
                      help='Path to output file (optional)')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        try:
            success = run_proxy_correlation_gate(
                validation_file=args.validation_file,
                output_file=args.output_file
            )
            if success:
                logger.info("Gate check passed.")
                sys.exit(0)
            else:
                logger.info("Gate check passed with warnings (CI mode).")
                sys.exit(0)
        except SystemExit as e:
            raise
        except Exception as e:
            log_fatal(f"Gate check failed: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()