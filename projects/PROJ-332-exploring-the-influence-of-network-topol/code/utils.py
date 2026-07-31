import logging
import csv
import os
from typing import Dict, Any, List, Optional

# Define the canonical fieldnames matching the schema in T004c
# This list must be kept in sync with specs/001-network-topology-thermal/contracts/simulation_result.schema.yaml
SIMULATION_RESULT_FIELDNAMES = [
    'seed',
    'N',
    'p',
    'avg_degree',
    'conductivity',
    'connectivity_probability',
    'percolation_threshold',
    'convergence_rate',
    'pilot_variance',
    'required_sample_size',
    'final_sample_size',
    'adjustment_triggered',
    'adjustment_reason'
]

def setup_logging(level: int = logging.INFO, log_file: str = 'simulation.log') -> logging.Logger:
    """
    Setup basic logging configuration.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Name of the log file to write to.
    
    Returns:
        The root logger instance.
    """
    # Avoid adding multiple handlers if logging is already configured
    if logging.getLogger().handlers:
        return logging.getLogger()

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    return logging.getLogger()

def write_csv_row(filepath: str, row: Dict[str, Any], fieldnames: Optional[List[str]] = None) -> None:
    """
    Append a row to the CSV file, creating it with headers if it doesn't exist.
    
    This function ensures that the CSV file matches the schema defined in T004c.
    If the file exists, it appends the row. If not, it writes the header and the row.
    
    Args:
        filepath: Path to the CSV file.
        row: Dictionary containing the row data. Keys must match the fieldnames.
        fieldnames: Optional list of fieldnames. Defaults to SIMULATION_RESULT_FIELDNAMES.
    """
    if fieldnames is None:
        fieldnames = SIMULATION_RESULT_FIELDNAMES
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    
    file_exists = os.path.exists(filepath)
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        
        # Ensure all required fields are present, filling missing ones with empty string or 0
        write_row = {}
        for k in fieldnames:
            val = row.get(k)
            if val is None:
                # Provide sensible defaults for numeric fields to avoid empty cells if possible,
                # but strictly follow schema. If schema expects numbers, we might want 0.0.
                # For now, use empty string to let the CSV reader handle it or downstream logic.
                # However, to prevent CSV errors, we default to empty string if key missing.
                write_row[k] = ''
            else:
                write_row[k] = val
        
        writer.writerow(write_row)

def format_error(e: Exception) -> str:
    """
    Format exception for logging.
    
    Args:
        e: The exception instance.
    
    Returns:
        A formatted string representation of the exception.
    """
    return f"{type(e).__name__}: {str(e)}"