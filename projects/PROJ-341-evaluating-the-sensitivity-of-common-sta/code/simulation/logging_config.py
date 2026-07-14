"""
Logging configuration and utility functions for the simulation pipeline.
Provides centralized logging setup, logger retrieval, and specific logging helpers
for reproducibility debugging and simulation step tracking.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Global logger instance to be configured once
_logger: Optional[logging.Logger] = None
_log_file_path: Optional[str] = None

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure the root logger for the simulation pipeline.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Path to log file. If None, logs to stdout only.
        console_output: Whether to log to console as well.
    
    Returns:
        Configured logger instance.
    """
    global _logger, _log_file_path
    
    # Create logger
    _logger = logging.getLogger('llmXive_simulation')
    _logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates on re-calls
    _logger.handlers.clear()
    
    # Formatter with detailed info for reproducibility debugging
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
        _log_file_path = log_file
    
    _logger.info("Logging system initialized")
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a specific name.
    
    Args:
        name: Optional name for the logger (e.g., 'simulation.test_runner')
    
    Returns:
        Logger instance.
    """
    global _logger
    if _logger is None:
        # Auto-initialize if not set
        setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger

def log_simulation_params(
    sample_sizes: list,
    effect_sizes: list,
    test_types: list,
    alpha: float,
    iterations: int,
    seed: int,
    logger: Optional[logging.Logger] = None
):
    """
    Log the simulation configuration parameters.
    
    Args:
        sample_sizes: List of sample sizes to test
        effect_sizes: List of effect sizes to test
        test_types: List of test types (t-test, anova, chi-squared)
        alpha: Significance level
        iterations: Number of iterations per condition
        seed: Random seed
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.config')
    log.info("=== Simulation Configuration ===")
    log.info(f"Sample sizes: {sample_sizes}")
    log.info(f"Effect sizes: {effect_sizes}")
    log.info(f"Test types: {test_types}")
    log.info(f"Alpha level: {alpha}")
    log.info(f"Iterations per condition: {iterations}")
    log.info(f"Random seed: {seed}")
    log.info("================================")

def log_seed_usage(seed: int, iteration: int, logger: Optional[logging.Logger] = None):
    """
    Log the usage of a specific random seed for an iteration.
    
    Args:
        seed: The seed value used
        iteration: The iteration number
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.seeds')
    log.debug(f"Iteration {iteration}: Seed {seed} used")

def log_iteration_status(
    iteration: int,
    total_iterations: int,
    current_n: int,
    current_effect: float,
    current_test: str,
    logger: Optional[logging.Logger] = None
):
    """
    Log the progress of the simulation iteration.
    
    Args:
        iteration: Current iteration number
        total_iterations: Total number of iterations
        current_n: Current sample size
        current_effect: Current effect size
        current_test: Current test type
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.progress')
    progress = (iteration / total_iterations) * 100
    log.info(f"[{iteration:05d}/{total_iterations:05d}] ({progress:5.1f}%) "
             f"n={current_n}, effect={current_effect:.3f}, test={current_test}")

def log_test_result(
    test_type: str,
    n: int,
    effect_size: float,
    p_value: float,
    alpha: float,
    rejected: bool,
    fallback_used: bool = False,
    warning_issued: bool = False,
    logger: Optional[logging.Logger] = None
):
    """
    Log the result of a single statistical test.
    
    Args:
        test_type: Type of test performed
        n: Sample size
        effect_size: Effect size used
        p_value: Calculated p-value
        alpha: Significance threshold
        rejected: Whether null hypothesis was rejected
        fallback_used: Whether a fallback test was used (e.g., Fisher's)
        warning_issued: Whether a warning about assumptions was issued
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.results')
    status = "REJECTED" if rejected else "FAILED"
    fallback_str = " [FALLBACK]" if fallback_used else ""
    warning_str = " [WARNING]" if warning_issued else ""
    
    log.debug(f"{test_type} (n={n}, effect={effect_size:.3f}): "
             f"p={p_value:.6f} -> {status} (alpha={alpha}){fallback_str}{warning_str}")

def log_warning_assumption_violated(
    assumption: str,
    condition: str,
    recommended_action: str,
    logger: Optional[logging.Logger] = None
):
    """
    Log a warning about a violated statistical assumption.
    
    Args:
        assumption: Name of the violated assumption
        condition: Description of the condition causing violation
        recommended_action: Suggested action to take
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.warnings')
    log.warning(f"ASSUMPTION VIOLATED: {assumption}")
    log.warning(f"  Condition: {condition}")
    log.warning(f"  Recommended: {recommended_action}")

def log_fallback_triggered(
    test_type: str,
    reason: str,
    fallback_test: str,
    logger: Optional[logging.Logger] = None
):
    """
    Log when a fallback statistical test is triggered.
    
    Args:
        test_type: Original test type
        reason: Reason for fallback
        fallback_test: Name of fallback test used
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.fallbacks')
    log.info(f"FALLBACK TRIGGERED: {test_type} -> {fallback_test}")
    log.info(f"  Reason: {reason}")

def log_output_file_written(
    file_path: str,
    record_count: int,
    logger: Optional[logging.Logger] = None
):
    """
    Log when an output file is written.
    
    Args:
        file_path: Path to the output file
        record_count: Number of records written
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.io')
    log.info(f"OUTPUT WRITTEN: {file_path} ({record_count} records)")

def log_error_details(
    error_type: str,
    error_message: str,
    context: Dict[str, Any],
    logger: Optional[logging.Logger] = None
):
    """
    Log detailed error information for debugging.
    
    Args:
        error_type: Type of error (e.g., ValueError, RuntimeError)
        error_message: Error message
        context: Dictionary of contextual variables at error time
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.errors')
    log.error(f"ERROR: {error_type} - {error_message}")
    log.error(f"Context: {json.dumps(context, default=str)}")

def log_shutdown(logger: Optional[logging.Logger] = None):
    """
    Log when the simulation process is shutting down.
    
    Args:
        logger: Logger instance (uses default if None)
    """
    log = logger or get_logger('simulation.system')
    log.info("Simulation process shutting down. All logging handlers flushed.")

def get_log_file_path() -> Optional[str]:
    """
    Get the path to the log file if one was configured.
    
    Returns:
        Path to log file or None if logging to console only.
    """
    return _log_file_path
