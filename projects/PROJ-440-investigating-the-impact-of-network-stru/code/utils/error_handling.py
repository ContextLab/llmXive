import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Define valid error types as per specification
VALID_ERROR_TYPES = {
    'NETWORKX_ERROR',
    'METRIC_CALC_FAILURE',
    'KS_TEST_FAIL',
    'SOLVE_IVP_CONVERGENCE_FAIL',
    'FIT_R2_LOW',
    'NUMERICAL_INSTABILITY'
}

class SimulationError(Exception):
    """Custom exception for simulation-related errors."""
    pass

class ConvergenceError(Exception):
    """Custom exception for convergence-related errors."""
    pass

def log_generation_failure(graph_id: str, error_type: str, message: str, log_path: str = "state/failedGraphs.log") -> None:
    """
    Log a graph generation failure to the specified log file.

    Format: GRAPH_ID|ISO8601_TIMESTAMP|ERROR_TYPE|MESSAGE

    Args:
        graph_id: The unique identifier of the graph that failed.
        error_type: One of the VALID_ERROR_TYPES.
        message: The error message or description.
        log_path: Path to the log file (default: state/failedGraphs.log).
    
    Raises:
        ValueError: If error_type is not in VALID_ERROR_TYPES.
    """
    if error_type not in VALID_ERROR_TYPES:
        raise ValueError(f"Invalid error_type '{error_type}'. Must be one of: {VALID_ERROR_TYPES}")
    
    timestamp = datetime.utcnow().isoformat()
    log_entry = f"{graph_id}|{timestamp}|{error_type}|{message}\n"
    
    # Ensure the directory exists
    import os
    log_dir = os.path.dirname(log_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    logging.warning(f"Logged generation failure for {graph_id}: {error_type} - {message}")

def handle_simulation_failure(graph_id: str, error: Exception, log_path: str = "state/simulation_failures.log") -> None:
    """
    Handle a simulation failure by determining the error type and logging it.

    Args:
        graph_id: The unique identifier of the graph that failed.
        error: The exception that was raised.
        log_path: Path to the log file (default: state/simulation_failures.log).
    """
    error_type = 'SOLVE_IVP_CONVERGENCE_FAIL'
    message = str(error)

    # Determine error type based on exception content or type
    if 'convergence' in str(error).lower() or 'convergence' in type(error).__name__.lower():
        error_type = 'SOLVE_IVP_CONVERGENCE_FAIL'
    elif 'fit' in str(error).lower() or 'r2' in str(error).lower() or 'R2' in str(error):
        error_type = 'FIT_R2_LOW'
    elif 'numerical' in str(error).lower():
        error_type = 'NUMERICAL_INSTABILITY'
    
    log_generation_failure(graph_id, error_type, message, log_path)

def log_non_convergence(graph_id: str, message: str, log_path: str = "state/simulation_failures.log") -> None:
    """
    Log a non-convergence event for a simulation.

    Args:
        graph_id: The unique identifier of the graph.
        message: Description of the non-convergence.
        log_path: Path to the log file.
    """
    log_generation_failure(graph_id, 'SOLVE_IVP_CONVERGENCE_FAIL', message, log_path)

def validate_simulation_result(result: Dict[str, Any]) -> bool:
    """
    Validate the result of a simulation.

    Args:
        result: Dictionary containing simulation results.

    Returns:
        True if valid, False otherwise.
    """
    # Basic validation: check for required keys
    required_keys = ['decay_rate', 'r_squared', 'status']
    return all(key in result for key in required_keys)

def filter_failed_results(results: List[Dict[str, Any]], failed_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Filter out results that correspond to failed graph IDs.

    Args:
        results: List of result dictionaries.
        failed_ids: List of graph IDs that failed.

    Returns:
        Filtered list of results.
    """
    failed_set = set(failed_ids)
    return [r for r in results if r.get('graph_id') not in failed_set]