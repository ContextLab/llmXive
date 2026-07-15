import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

_logger = None
_log_file_path = None

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup the global logger.
    
    Args:
        log_file: Optional path to log file. Defaults to data/logs/simulation.log
        
    Returns:
        Configured logger instance
    """
    global _logger, _log_file_path
    
    if _logger is not None:
        return _logger
    
    # Default log file path
    if log_file is None:
        log_dir = "data/logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"simulation_{timestamp}.log")
    
    _log_file_path = log_file
    
    # Create logger
    _logger = logging.getLogger('sim_logger')
    _logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    _logger.handlers = []
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    _logger.addHandler(fh)
    _logger.addHandler(ch)
    
    return _logger

def get_logger() -> Optional[logging.Logger]:
    """Get the global logger instance."""
    return _logger

def log_simulation_params(logger: logging.Logger, args: Any):
    """Log simulation parameters."""
    params = {
        'mode': args.mode,
        'test': args.test,
        'min_n': args.min_n,
        'max_n': args.max_n,
        'step_n': args.step_n,
        'effect_sizes': args.effect_sizes,
        'hypotheses': args.hypotheses,
        'alpha': args.alpha,
        'iterations': args.iterations,
        'seed': args.seed,
        'timestamp': datetime.now().isoformat()
    }
    logger.info(f"Simulation parameters: {json.dumps(params, indent=2)}")

def log_seed_usage(logger: logging.Logger, seed: int, iteration: int):
    """Log seed usage for reproducibility."""
    logger.debug(f"Iteration {iteration} using seed: {seed}")

def log_iteration_status(logger: logging.Logger, iteration: int, total: int, status: str):
    """Log iteration status."""
    logger.info(f"Iteration {iteration}/{total}: {status}")

def log_test_result(logger: logging.Logger, test_type: str, p_value: float, hypothesis: str):
    """Log test result."""
    logger.debug(f"Test {test_type}, Hypothesis {hypothesis}, p-value: {p_value}")

def log_warning_assumption_violated(logger: logging.Logger, test_type: str, assumption: str):
    """Log assumption violation warning."""
    logger.warning(f"Assumption violated for {test_type}: {assumption}")

def log_fallback_triggered(logger: logging.Logger, original_test: str, fallback_test: str):
    """Log fallback test trigger."""
    logger.warning(f"Test {original_test} triggered fallback to {fallback_test}")

def log_output_file_written(logger: logging.Logger, file_path: str, count: int):
    """Log output file write."""
    logger.info(f"Wrote {count} records to {file_path}")

def log_error_details(logger: logging.Logger, error: Exception):
    """Log error details."""
    logger.error(f"Error occurred: {str(error)}")
    import traceback
    logger.error(traceback.format_exc())

def log_shutdown(logger: logging.Logger):
    """Log shutdown."""
    if logger:
        logger.info("Simulation shutdown complete")

def get_log_file_path() -> Optional[str]:
    """Get the path to the log file."""
    return _log_file_path
