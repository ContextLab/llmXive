"""
Comprehensive logging configuration for the simulation pipeline.
Ensures reproducibility debugging by capturing all simulation steps,
parameters, seeds, and outcomes.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[str] = None

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(log_level: str = "INFO", log_dir: str = "data/logs") -> str:
    """
    Configure the root logger for the simulation pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
    
    Returns:
        Path to the created log file
    """
    global _logger, _log_file_path
    
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _log_file_path = os.path.join(log_dir, f"simulation_{timestamp}.log")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(_log_file_path)
    file_handler.setLevel(logging.DEBUG)  # Capture all levels in file
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(file_handler)
    
    # Console handler (optional, for immediate feedback)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)
    
    _logger = root_logger
    
    # Log initialization
    root_logger.info(f"Logging initialized at {_log_file_path}")
    root_logger.info(f"Log level set to {log_level}")
    
    return _log_file_path

def get_logger(name: str = "llmXive.simulation") -> logging.Logger:
    """
    Get a named logger instance for a specific module.
    
    Args:
        name: Logger name (typically module name)
    
    Returns:
        Configured logger instance
    """
    global _logger
    if _logger is None:
        # Auto-setup if not initialized
        setup_logging()
    
    return logging.getLogger(name)

def log_simulation_params(params: Dict[str, Any]) -> None:
    """
    Log simulation configuration parameters.
    
    Args:
        params: Dictionary of simulation parameters
    """
    logger = get_logger("simulation.config")
    logger.info("Starting simulation with parameters:")
    logger.info(json.dumps(params, indent=2, default=str))

def log_seed_usage(seed: int, context: str = "") -> None:
    """
    Log the usage of a random seed for reproducibility tracking.
    
    Args:
        seed: The random seed value
        context: Description of where the seed is used
    """
    logger = get_logger("simulation.seeds")
    msg = f"Seed {seed} used for {context}"
    logger.debug(msg)

def log_iteration_status(iteration: int, total: int, condition: Dict[str, Any]) -> None:
    """
    Log progress of simulation iterations.
    
    Args:
        iteration: Current iteration number
        total: Total iterations
        condition: Current condition parameters
    """
    logger = get_logger("simulation.progress")
    percent = (iteration / total) * 100
    logger.info(f"Iteration {iteration}/{total} ({percent:.1f}%) | Condition: {condition}")

def log_test_result(test_name: str, sample_size: int, effect_size: float, 
                    p_value: float, hypothesis: str, seed: int, 
                    fallback_triggered: bool = False) -> None:
    """
    Log the result of a single statistical test.
    
    Args:
        test_name: Name of the statistical test
        sample_size: Sample size used
        effect_size: Effect size parameter
        p_value: Resulting p-value
        hypothesis: 'null' or 'alternative'
        seed: Random seed used
        fallback_triggered: Whether fallback logic was triggered
    """
    logger = get_logger("simulation.results")
    msg = (f"Test: {test_name} | n={sample_size} | effect={effect_size} | "
           f"p={p_value:.6f} | H={hypothesis} | seed={seed}")
    if fallback_triggered:
        msg += " | FALLBACK TRIGGERED"
    logger.debug(msg)

def log_warning_assumption_violated(test_name: str, assumption: str, 
                                    sample_size: int) -> None:
    """
    Log a warning when a statistical test assumption is violated.
    
    Args:
        test_name: Name of the statistical test
        assumption: Which assumption was violated
        sample_size: Current sample size
    """
    logger = get_logger("simulation.warnings")
    msg = f"WARNING: {test_name} assumption '{assumption}' violated at n={sample_size}"
    logger.warning(msg)

def log_fallback_triggered(test_name: str, fallback_method: str, reason: str) -> None:
    """
    Log when a fallback statistical method is triggered.
    
    Args:
        test_name: Original test name
        fallback_method: Fallback method used
        reason: Reason for fallback
    """
    logger = get_logger("simulation.fallbacks")
    msg = f"FALLBACK: {test_name} -> {fallback_method} | Reason: {reason}"
    logger.warning(msg)

def log_output_file_written(filepath: str, record_count: int) -> None:
    """
    Log when output files are written.
    
    Args:
        filepath: Path to the output file
        record_count: Number of records written
    """
    logger = get_logger("simulation.io")
    logger.info(f"Output written to {filepath} ({record_count} records)")

def log_error_details(error: Exception, context: str = "") -> None:
    """
    Log detailed error information for debugging.
    
    Args:
        error: The exception object
        context: Additional context about where the error occurred
    """
    logger = get_logger("simulation.errors")
    logger.error(f"ERROR in {context}: {type(error).__name__}: {str(error)}", exc_info=True)

def log_shutdown() -> None:
    """
    Log simulation shutdown and summary.
    """
    logger = get_logger("simulation.lifecycle")
    logger.info("Simulation pipeline shutdown complete.")
    if _log_file_path:
        logger.info(f"Log file available at: {_log_file_path}")

def get_log_file_path() -> Optional[str]:
    """
    Get the path to the current log file.
    
    Returns:
        Path to log file or None if not initialized
    """
    return _log_file_path
