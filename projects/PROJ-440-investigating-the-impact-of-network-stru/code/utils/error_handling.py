import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class SimulationError(Exception):
    """Custom exception for simulation errors."""
    pass

class ConvergenceError(Exception):
    """Custom exception for convergence failures."""
    pass

def handle_simulation_failure(graph_id: str, error_type: str, error_message: str) -> Dict[str, Any]:
    """
    Handle simulation failure by logging and returning error metadata.
    
    Args:
        graph_id: Identifier of the failed graph
        error_type: Type of error (e.g., 'non-convergence', 'integration-failed')
        error_message: Detailed error message
        
    Returns:
        Dictionary with error metadata
    """
    error_record = {
        'graph_id': graph_id,
        'error_type': error_type,
        'error_message': error_message,
        'status': 'failed'
    }
    
    logger.error(f"Simulation failed for graph {graph_id}: {error_type} - {error_message}")
    return error_record

def log_non_convergence(graph_id: str, reason: str) -> None:
    """
    Log a non-convergence event with specific details.
    
    Args:
        graph_id: Identifier of the graph
        reason: Specific reason for non-convergence
    """
    logger.error(f"Non-convergence detected for graph {graph_id}: {reason}")

def validate_simulation_result(result: Optional[Dict[str, Any]], graph_id: str) -> bool:
    """
    Validate that a simulation result is valid and usable.
    
    Args:
        result: Simulation result dictionary
        graph_id: Identifier of the graph
        
    Returns:
        True if result is valid, False otherwise
    """
    if result is None:
        log_non_convergence(graph_id, "Result is None")
        return False
    
    if 'decay_rate' not in result or result['decay_rate'] is None:
        log_non_convergence(graph_id, "Missing or None decay_rate")
        return False
    
    if 'r_squared' not in result or result['r_squared'] < 0.95:
        log_non_convergence(graph_id, f"Insufficient fit quality: R²={result.get('r_squared', 0)}")
        return False
    
    return True

def filter_failed_results(results: List[Dict[str, Any]], error_log_path: str = 'logs/simulation_errors.log') -> List[Dict[str, Any]]:
    """
    Filter out failed results and log them to a separate file.
    
    Args:
        results: List of simulation results
        error_log_path: Path to error log file
        
    Returns:
        List of valid results
    """
    valid_results = []
    failed_results = []
    
    for result in results:
        if result.get('status') == 'failed' or result.get('decay_rate') is None:
            failed_results.append(result)
        else:
            valid_results.append(result)
    
    if failed_results:
        logger.warning(f"Excluding {len(failed_results)} failed simulations from analysis")
        
        # Write error log
        with open(error_log_path, 'w') as f:
            f.write("Simulation Errors Log\n")
            f.write("=" * 50 + "\n\n")
            for error in failed_results:
                f.write(f"Graph ID: {error.get('graph_id', 'N/A')}\n")
                f.write(f"Error Type: {error.get('error_type', 'N/A')}\n")
                f.write(f"Message: {error.get('error_message', 'N/A')}\n")
                f.write("-" * 30 + "\n")
        
        logger.info(f"Error log written to {error_log_path}")
    
    return valid_results
