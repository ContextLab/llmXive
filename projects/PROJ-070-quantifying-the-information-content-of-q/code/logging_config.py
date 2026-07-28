import logging
import sys
import warnings
import numpy as np
from typing import Optional, List, Dict, Any

# Custom exception for numerical instability events
class E_NUMERICAL_INSTABILITY(Exception):
    """Raised when numerical instability (NaN/Inf) is detected in data."""
    pass

# Custom exception for data exclusion events
class E_DATA_EXCLUSION(Exception):
    """Raised when data points are excluded due to validation failures."""
    pass

# Global list to track numerical instability events
_instability_events: List[Dict[str, Any]] = []
_exclusion_events: List[Dict[str, Any]] = []

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Setup the logging infrastructure to track numerical instabilities and data exclusion.
    Returns the configured root logger.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Add a file handler for detailed audit trail
        try:
            file_handler = logging.FileHandler('logs/numerical_audit.log')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logger.warning(f"Could not create file handler for audit log: {e}")

    # Suppress generic numpy warnings that might clutter output
    warnings.filterwarnings('ignore', category=UserWarning, module='numpy')
    
    return logger

def check_numerical_stability(data: np.ndarray, context: str = "Unknown") -> bool:
    """
    Check if the provided numpy array contains NaN or Inf values.
    
    Args:
        data: The numpy array to check
        context: A string describing the source/context of the data
        
    Returns:
        True if the data is numerically stable, False otherwise
        
    Raises:
        E_NUMERICAL_INSTABILITY: If NaN or Inf values are detected
    """
    if not isinstance(data, np.ndarray):
        try:
            data = np.asarray(data)
        except Exception as e:
            raise E_NUMERICAL_INSTABILITY(f"Cannot convert data to numpy array: {e}")
    
    has_nan = np.any(np.isnan(data))
    has_inf = np.any(np.isinf(data))
    
    if has_nan or has_inf:
        event = {
            'context': context,
            'has_nan': bool(has_nan),
            'has_inf': bool(has_inf),
            'nan_count': int(np.sum(np.isnan(data))) if has_nan else 0,
            'inf_count': int(np.sum(np.isinf(data))) if has_inf else 0,
            'shape': data.shape,
            'dtype': str(data.dtype)
        }
        _instability_events.append(event)
        logger = logging.getLogger("llmXive")
        logger.error(f"NUMERICAL INSTABILITY DETECTED in {context}: "
                    f"NaN={event['nan_count']}, Inf={event['inf_count']}, "
                    f"Shape={event['shape']}, Dtype={event['dtype']}")
        raise E_NUMERICAL_INSTABILITY(f"Numerical instability detected in {context}: "
                                     f"{event['nan_count']} NaNs, {event['inf_count']} Infs")
    
    return True

def log_data_exclusion(reason: str, context: str = "Unknown", 
                     affected_indices: Optional[List[int]] = None,
                     affected_count: Optional[int] = None):
    """
    Log a data exclusion event with detailed context.
    
    Args:
        reason: The reason for exclusion
        context: The source/context where exclusion occurred
        affected_indices: List of indices that were excluded (optional)
        affected_count: Number of excluded items (optional)
    """
    event = {
        'reason': reason,
        'context': context,
        'affected_indices': affected_indices,
        'affected_count': affected_count,
        'timestamp': logging.Formatter('%(asctime)s').formatTime(logging.LogRecord(
            'temp', logging.INFO, '', 0, '', (), None
        ))
    }
    _exclusion_events.append(event)
    logger = logging.getLogger("llmXive")
    logger.warning(f"DATA EXCLUSION in {context}: {reason} "
                  f"(Count: {affected_count}, Indices: {affected_indices})")

def get_instability_events() -> List[Dict[str, Any]]:
    """
    Retrieve all recorded numerical instability events.
    
    Returns:
        List of dictionaries containing instability event details
    """
    return _instability_events.copy()

def get_exclusion_events() -> List[Dict[str, Any]]:
    """
    Retrieve all recorded data exclusion events.
    
    Returns:
        List of dictionaries containing exclusion event details
    """
    return _exclusion_events.copy()

def clear_event_logs():
    """Clear all recorded instability and exclusion events."""
    _instability_events.clear()
    _exclusion_events.clear()

# Initialize global logger instance
logger = setup_logging()
